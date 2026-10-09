"""Finite chosen-spec behavioral checks, with orthogonal unknown dimensions.

The oracle consumes pinned decision versions, never the implementation's own
configuration. It provides no independent source about requirement fitness.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
import json
import math
from typing import Mapping

from .artifacts import ChangeProposal, DECISION_IDS, FAILURE_CATEGORIES, Goal
from .clock import require_tick
from .events import CausalLink, EntityRef, EventHistory


@dataclass(frozen=True, slots=True)
class BehavioralCheck:
    category: str
    expected: tuple
    actual: tuple

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


@dataclass(frozen=True, slots=True)
class AssuranceAssessment:
    dimension: str
    status: str
    method: str
    subject: EntityRef
    source_dependencies: tuple[EntityRef, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Verification:
    proposal: ChangeProposal
    checks: tuple[BehavioralCheck, ...]
    assessments: tuple[AssuranceAssessment, ...]


def verify_proposal(proposal: ChangeProposal, parameters: Mapping[str, int]) -> Verification:
    """Exercise every supported failure class against its pinned interpretation.

    Fixed operation IDs are engineering examples, not sampled world outcomes.
    No all-correct flag, green-to-deploy transition, evidence grant or belief update.
    """
    choices = {d.decision_id: d.selected for d in proposal.decisions}
    if len(proposal.decisions) != 6 or set(choices) != set(DECISION_IDS):
        raise ValueError('verification requires exactly all six pinned decisions')
    if choices['retry_count'] not in ('none', 'one', 'three') or choices['retryable_types'] not in (
        'transient_only', 'all_failures'
    ):
        raise ValueError('verification requires explicit refinement')
    limit = parameters[{'none': 'retry.none', 'one': 'retry.one', 'three': 'retry.three'}[choices['retry_count']]]
    checks = []
    for category in FAILURE_CATEGORIES:
        allowed = choices['retryable_types'] == 'all_failures' or category == 'transient'
        if category in ('soft_decline', 'hard_decline'):
            allowed &= (choices['declined_handling'] == 'retry_all'
                        or choices['declined_handling'] == 'soft_only' and category == 'soft_decline')
        expected = []
        for ordinal in range(1, limit + 1) if allowed else ():
            if choices['backoff'] == 'immediate':
                delay = 0
            elif choices['backoff'] == 'fixed':
                delay = ordinal * parameters['backoff.fixed']
            else:
                delay = sum(min(parameters['backoff.fixed'] * 2 ** n, parameters['backoff.capped'])
                            for n in range(ordinal))
            key = {'stable_key': 'verification.payment',
                   'new_key': f'verification.payment:retry:{ordinal}', 'unspecified': None}[choices['idempotency']]
            expected.append((ordinal, delay, key, choices['audit_requirement']))
        checks.append(BehavioralCheck(category, tuple(expected),
                                      proposal.behavior.plan(category, 'verification.payment')))
    status = 'pass' if all(c.passed for c in checks) else 'fail'
    assessments = tuple(AssuranceAssessment(
        dimension, status if dimension in ('implementation_conformance', 'verification_status') else 'unknown',
        'finite_chosen_spec_checks' if dimension in ('implementation_conformance', 'verification_status') else 'unassessed',
        proposal.ref, proposal.decision_refs,
        tuple(f'{proposal.proposal_id}:check:{c.category}' for c in checks)
        if dimension in ('implementation_conformance', 'verification_status') else (),
    ) for dimension in ('implementation_conformance', 'verification_status', 'requirement_conformance',
                        'architecture_conformance', 'policy_security_conformance', 'validation_status', 'outcome_fitness'))
    return Verification(proposal, tuple(checks), assessments)


@dataclass(frozen=True, slots=True)
class ProductionAssessment:
    """A finite observation-window assessment, not proof of a causal remedy."""
    assessment: AssuranceAssessment
    goal: EntityRef
    sample_count: int
    abandonment_rate: float | None
    minimum_samples: int
    revision_margin: float
    event_id: str


def assess_production(history: EventHistory, deployment: EntityRef, goal: Goal,
                      observation_ids: tuple[str, ...], *, tick: int, command_id: str,
                      minimum_samples: int, revision_margin: float) -> ProductionAssessment:
    """Assess only recorded available observations of one pinned deployment.

    Each deployment/operation is one sample, even through repeated citations.
    A miss beyond the declared margin challenges this deployment's interpretation;
    it neither identifies a faulty decision nor validates an alternative policy.
    Pending samples, an incomplete window and a narrow miss remain visible.
    """
    require_tick(tick)
    require_tick(minimum_samples)
    if minimum_samples == 0:
        raise ValueError('minimum_samples must be positive')
    if (type(revision_margin) not in (int, float) or not 0 <= revision_margin <= 1
            or not math.isfinite(revision_margin)):
        raise ValueError('revision_margin must be a finite rate in [0, 1]')
    if type(observation_ids) is not tuple or any(type(i) is not str for i in observation_ids):
        raise TypeError('observation IDs must be an immutable tuple of strings')
    if type(deployment) is not EntityRef or deployment.entity_type != 'deployment':
        raise ValueError('expected a deployment reference')
    if (type(goal) is not Goal or goal.measure != 'failed_payment_abandonment_per_eligible_attempt'
            or type(goal.target) not in (int, float) or not 0 <= goal.target <= 1):
        raise ValueError('unsupported goal measure/target')
    events = {e.event_id: e for e in history.events}
    shipped = next((e for e in history.events if e.event_type == 'DeploymentCompleted'
                    and deployment in e.entities), None)
    declared = next((e for e in history.events if e.event_type == 'GoalDeclared'
                     and goal.ref in e.entities), None)
    if shipped is None or declared is None or declared.payload != json.loads(json.dumps(asdict(goal))):
        raise ValueError('deployment and goal must match recorded versions')
    work = next((events[p.event_id] for p in shipped.parents
                 if events[p.event_id].event_type == 'ChangeProposalCreated'), None)
    if work is None or not any(e.event_type == 'WorkItemCreated' and goal.ref in e.entities
                              and any(r.entity_type == 'work_item' and r in work.entities for r in e.entities)
                              for e in history.events):
        raise ValueError('goal is not linked to this deployment work item')
    pins = tuple(EntityRef(**r) for r in shipped.payload['decision_refs'])
    selected = {}
    window_end = shipped.tick + goal.observation_window
    for event_id in observation_ids:
        observed = events.get(event_id)
        if (observed is None or observed.event_type != 'OutcomeObserved' or observed.tick > tick
                or observed.payload['deployment'] != deployment.as_dict()
                or observed.payload['decision_refs'] != shipped.payload['decision_refs']):
            raise ValueError('evidence must be available observations of this deployment version')
        outcome = next((events[p.event_id] for p in observed.parents
                        if events[p.event_id].event_type == 'PaymentOutcome'), None)
        if (outcome is None or outcome.payload['deployment'] != deployment.as_dict()
                or outcome.payload['operation_id'] != observed.payload['operation_id']
                or any(outcome.payload[k] != observed.payload[k]
                       for k in ('abandoned', 'completed', 'duplicate_charges', 'outcome_tick'))):
            raise ValueError('observation must retain its recorded outcome lineage')
        # Window uses physical outcome time, not the time delayed feedback arrived.
        if not shipped.tick <= observed.payload['outcome_tick'] <= window_end:
            continue
        key = observed.payload['operation_id']
        if key not in shipped.payload['workload_operations']:
            raise ValueError('observation has no admitted operation')
        if key in selected and selected[key].payload['abandoned'] != observed.payload['abandoned']:
            raise ValueError('conflicting observations for one source operation')
        selected[key] = observed
    ordered = tuple(sorted(selected.values(), key=lambda e: e.sequence))
    count = len(ordered)
    abandoned = sum(e.payload['abandoned'] for e in ordered)
    rate = abandoned / count if count else None
    # All admitted operations must be observed in this finite window to avoid
    # selecting a convenient subset; larger window/streaming estimators are deferred.
    complete = count == len(shipped.payload['workload_operations'])
    if count < minimum_samples or not complete:
        status = 'pending'
    elif Fraction(abandoned, count) <= Fraction(str(goal.target)):
        status = 'pass'
    elif Fraction(abandoned, count) - Fraction(str(goal.target)) >= Fraction(str(revision_margin)):
        status = 'fail'
    else:
        status = 'unknown'
    assessment = AssuranceAssessment('outcome_fitness', status, 'finite_observed_goal_window',
                                     deployment, (goal.ref,) + pins,
                                     tuple(e.event_id for e in ordered))
    payload = json.loads(json.dumps(asdict(assessment)))
    payload.update(goal=goal.ref.as_dict(), sample_count=count, abandonment_rate=rate,
                   minimum_samples=minimum_samples, revision_margin=revision_margin,
                   window_end=window_end, complete=complete, model_version='learning-loops-v1')
    event = history.append(tick=tick, event_type='ProductionAssessed', command_id=command_id,
        correlation_id=command_id, entities=(deployment, goal.ref) + pins, payload=payload,
        parents=(CausalLink(shipped.event_id, 'association'), CausalLink(declared.event_id, 'association'))
                + tuple(CausalLink(e.event_id, 'supporting_evidence') for e in ordered))
    return ProductionAssessment(assessment, goal.ref, count, rate, minimum_samples,
                                revision_margin, event.event_id)
