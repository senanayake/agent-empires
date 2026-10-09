"""Finite chosen-spec behavioral checks, with orthogonal unknown dimensions.

The oracle consumes pinned decision versions, never the implementation's own
configuration. It provides no independent source about requirement fitness.
"""
from dataclasses import dataclass
from typing import Mapping

from .artifacts import ChangeProposal, DECISION_IDS, FAILURE_CATEGORIES
from .events import EntityRef


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
