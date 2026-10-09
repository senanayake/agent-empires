"""Headless PaymentCo delivery orchestration; simulation owns executable rules."""
from dataclasses import asdict, replace
import json
from types import MappingProxyType

from .scenarios import Scenario
from agent_empires.simulation.actors import require_text
from agent_empires.simulation.artifacts import (
    ChangeProposal, DeliveryJob, Goal, WorkItem, behavior_from_choices,
)
from agent_empires.simulation.assurance import Verification, verify_proposal
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.decisions import AuthorityGrant, AuthorityRegistry, Decisions
from agent_empires.simulation.events import CausalLink, EntityRef, EventHistory


def _payload(value) -> dict:
    """Convert immutable tuple fields to strict JSON arrays for event history."""
    return json.loads(json.dumps(asdict(value), allow_nan=False))


class DeliveryService:
    """One authored work item; multiple commands can pin different versions.

    Root grants are trusted setup. Initial policy catalog is not automatically
    enacted or copied into a worker's holdings. Existing explicit selections can
    be supplied through Decisions; missing choices use a fresh live view.
    Speed and cost apply per work item, paid once at start, for either Actor kind.
    Availability sampling and concurrent capacity constraints remain future rules.
    """
    def __init__(self, scenario: Scenario, *, run_id: str) -> None:
        self.scenario = scenario
        self.history = EventHistory(run_id)
        self.clock = SimulationClock()
        self.knowledge = scenario.instantiate_knowledge(self.history)
        self.authority = AuthorityRegistry(self.knowledge, self.history)
        self.decisions = Decisions(self.knowledge, self.authority, self.history)
        data = scenario.audit_data()
        self._actors = {a['actor_id']: a for a in data['actors']}
        self._profiles = {p['profile_id']: p for p in data['profiles']}
        self._parameters = {p['parameter_id']: p['value'] for p in data['parameters']}
        self.behavior_parameters = MappingProxyType({
            name: value for name, value in self._parameters.items()
            if name.startswith(('retry.', 'backoff.'))
        })
        for question in data['decisions']:
            self.decisions.register(scenario.question_for(question['decision_id']))
        for grant in data['grants']:
            self.authority.add_root(AuthorityGrant(**{**grant, 'options': tuple(grant['options'])}),
                                    tick=0, command_id='setup.' + grant['grant_id'], correlation_id='scenario.setup')
        g = data['goal']
        self.goal = Goal(g['goal_id'], data['intent'], g['measure'], self._parameters[g['target']],
                         self._parameters[g['observation_window']], tuple(g['separate_measures']))
        w = data['work_item']
        self.work_item = WorkItem(w['work_item_id'], self.goal.ref, w['text'], tuple(w['decision_ids']))
        goal_event = self.history.append(tick=0, event_type='GoalDeclared', command_id='setup.goal',
                                         correlation_id='delivery.setup', entities=(self.goal.ref,), payload=_payload(self.goal))
        self._work_event = self.history.append(
            tick=0, event_type='WorkItemCreated', command_id='setup.work', correlation_id='delivery.setup',
            entities=(self.work_item.ref, self.goal.ref), payload=_payload(self.work_item),
            parents=(CausalLink(goal_event.event_id, 'direct_cause'),),
        )
        self._requirements = {}
        for name in self.work_item.required_decisions:
            self._requirements[name] = self.history.append(
                tick=0, event_type='DecisionRequired', command_id='setup.required.' + name,
                correlation_id='delivery.setup', payload={'decision_id': name},
                entities=(self.work_item.ref, scenario.question_for(name).ref),
                parents=(CausalLink(self._work_event.event_id, 'direct_cause'),),
            )
        self._jobs: dict[str, DeliveryJob] = {}
        self._proposals: tuple[ChangeProposal, ...] = ()
        self.spent_resource_units = 0

    @property
    def proposals(self) -> tuple[ChangeProposal, ...]:
        return self._proposals

    def start(self, actor_id: str, *, command_id: str, defect: str | None = None) -> DeliveryJob:
        """Preflight all choices before creating facts, spending or scheduling."""
        require_text(command_id, 'command_id')
        if command_id in self._jobs:
            raise ValueError('duplicate delivery command')
        if defect not in (None, 'omit_retries'):
            raise ValueError('unknown implementation defect')
        if actor_id not in self._actors or any(
            e.event_type == 'ActorDeparted' and e.payload['actor_id'] == actor_id for e in self.history.events
        ):
            raise ValueError('work requires a present actor')
        if self.history.events[-1].tick > self.clock.now:
            raise ValueError('clock must reach latest recorded fact before starting work')
        view = self.knowledge.view_for(actor_id)
        choices, pending = {}, {}
        for name in self.work_item.required_decisions:
            versions = self.decisions.versions(name)
            if versions:
                choices[name] = versions[-1].selected
            else:
                profile = self.scenario.profile_for(actor_id, name)
                option, rationale = profile.propose(self.scenario.question_for(name), view)
                choices[name] = option
                pending[name] = (profile, option, rationale)
        behavior = behavior_from_choices(choices, self.behavior_parameters)
        if defect == 'omit_retries':
            behavior = replace(behavior, retry_count=0)
        pinned = []
        for name in self.work_item.required_decisions:
            if name in pending:
                profile, option, rationale = pending[name]
                version = self.decisions.select(
                    name, option, actor_id=actor_id, expected_version=0, tick=self.clock.now,
                    command_id=command_id + '.infer.' + name, correlation_id=command_id,
                    confidence=profile.confidence, rationale_holding_ids=rationale,
                    reason='capability preference over available exact claims',
                    missing_information=('unvalidated interpretation:' + name,),
                    parents=(CausalLink(self._requirements[name].event_id, 'direct_cause'),),
                )
            else:
                version = self.decisions.versions(name)[-1]
            pinned.append(version)
        profile = self._profiles[self._actors[actor_id]['profile_id']]
        duration, cost = (self._parameters[profile[name]] for name in ('work_ticks', 'work_cost'))
        finish_tick = self.clock.now + duration
        refs = tuple(d.ref for d in pinned)
        event = self.history.append(
            tick=self.clock.now, event_type='WorkStarted', command_id=command_id, correlation_id=command_id,
            entities=(self.work_item.ref, EntityRef('actor', actor_id, 1)) + refs,
            payload={'actor_id': actor_id, 'work_item': self.work_item.ref.as_dict(),
                     'decision_refs': [r.as_dict() for r in refs], 'completion_tick': finish_tick,
                     'resource_cost': cost, 'defect_injection': defect},
            parents=(CausalLink(self._work_event.event_id, 'direct_cause'),)
                    + tuple(CausalLink(d.event_id, 'direct_cause') for d in pinned),
        )
        job = DeliveryJob(command_id, actor_id, self.work_item.ref, tuple(pinned), behavior,
                          self.clock.now, finish_tick, cost, event.event_id)
        self.clock.schedule(finish_tick, command_id)
        self._jobs[command_id] = job
        self.spent_resource_units += cost
        return job

    def step(self) -> Verification | None:
        """Dispatch one completion and verification at simulated time, never ship."""
        scheduled = self.clock.pop_next()
        if scheduled is None:
            return None
        job = self._jobs[scheduled.command_id]
        proposal_id = 'proposal.' + job.command_id
        ref = EntityRef('change_proposal', proposal_id, 1)
        event = self.history.append(
            tick=self.clock.now, event_type='ChangeProposalCreated',
            command_id=job.command_id + '.complete', correlation_id=job.command_id,
            entities=(ref, job.work_item) + tuple(d.ref for d in job.decisions),
            payload={'behavior': asdict(job.behavior), 'decision_refs': [d.ref.as_dict() for d in job.decisions],
                     'unsupported_decisions': [d.ref.as_dict() for d in job.decisions
                                               if d.support != 'supported' or d.grant_ref is None
                                               or d.missing_information],
                     'resource_cost': job.resource_cost},
            parents=(CausalLink(job.event_id, 'direct_cause'),)
                    + tuple(CausalLink(d.event_id, 'direct_cause') for d in job.decisions),
        )
        proposal = ChangeProposal(proposal_id, job.work_item, job.actor_id, job.decisions, job.behavior,
                                  self.clock.now, job.resource_cost, event.event_id)
        verification = verify_proposal(proposal, self.behavior_parameters)
        self.history.append(
            tick=self.clock.now, event_type='VerificationCompleted', command_id=job.command_id + '.verify',
            correlation_id=job.command_id, entities=(proposal.ref,) + proposal.decision_refs,
            payload={'assessments': [_payload(a) for a in verification.assessments],
                     'checks': [dict(_payload(c), passed=c.passed) for c in verification.checks]},
            parents=(CausalLink(event.event_id, 'direct_cause'),),
        )
        self._proposals += (proposal,)
        return verification
