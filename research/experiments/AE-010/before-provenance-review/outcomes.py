"""Explicit toy payment exposure and delayed feedback, independent of Actor kind.

The caller supplies trusted world values and immutable pre-sampled workloads.
Only retries cost resources. Ambiguous failures can hide an already executed
operation; stable keys acknowledge it, while successful fresh-key execution can
duplicate it. Uncertainty/authority never enters the physical damage rule.
"""
from dataclasses import asdict, dataclass
import json
import math

from .actors import require_text
from .artifacts import ChangeProposal, FAILURE_CATEGORIES
from .clock import SimulationClock, require_tick
from .events import CausalLink, EntityRef, Event, EventHistory
from .randomness import NamedRandomness

MODEL_VERSION = 'payment-outcomes-v1'


def _probability(value: float) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('probability must be finite and between zero and one')


@dataclass(frozen=True, slots=True)
class WorldRules:
    world_id: str
    mix: tuple[float, ...]
    recovery: tuple[float, ...]
    duplicate_probability: float
    retry_cost: int
    abandonment_probability: float
    observation_lag: int
    workload_rate: int
    recovery_delay: int

    def __post_init__(self) -> None:
        require_text(self.world_id, 'world_id')
        for values in (self.mix, self.recovery):
            if type(values) is not tuple or len(values) != len(FAILURE_CATEGORIES):
                raise ValueError('world requires four immutable category probabilities')
            for value in values:
                _probability(value)
        if not math.isclose(sum(self.mix), 1, rel_tol=0, abs_tol=1e-12):
            raise ValueError('world mix must sum to one')
        for value in (self.duplicate_probability, self.abandonment_probability):
            _probability(value)
        for value in (self.retry_cost, self.observation_lag, self.workload_rate, self.recovery_delay):
            require_tick(value)


@dataclass(frozen=True, slots=True)
class PaymentInput:
    operation_id: str
    arrival_offset: int
    category: str
    hidden_commit_draw: float
    recovery_draws: tuple[float, ...]
    abandonment_draws: tuple[float, ...]

    def __post_init__(self) -> None:
        require_text(self.operation_id, 'operation_id')
        require_tick(self.arrival_offset)
        if self.category not in FAILURE_CATEGORIES:
            raise ValueError('unknown failure category')
        _probability(self.hidden_commit_draw)
        for draws, length in ((self.recovery_draws, 3), (self.abandonment_draws, 4)):
            if type(draws) is not tuple or len(draws) != length:
                raise ValueError('workload requires immutable bounded ordinal draws')
            for value in draws:
                _probability(value)
                if value == 1:
                    raise ValueError('draws must be in the half-open unit interval')
        if self.hidden_commit_draw == 1:
            raise ValueError('draws must be in the half-open unit interval')


def generate_workload(world: WorldRules, *, seed: int, arrival_window: int) -> tuple[PaymentInput, ...]:
    """Fixed failed-payment arrivals; keyed draws do not shift across strategies.

    Category and all potential retry/customer draws exist before shipping. World
    probabilities consume the same draws, permitting parameter sensitivity too.
    """
    require_tick(arrival_window)
    randomness = NamedRandomness(seed)
    payments = []
    for offset in range(arrival_window):
        for slot in range(world.workload_rate):
            operation = f'payment.{offset}.{slot}'
            def draw(name):
                return randomness.stream('payment-world.' + operation + '.' + name).random()
            category_draw = draw('category')
            cumulative = 0
            category = FAILURE_CATEGORIES[-1]
            for name, probability in zip(FAILURE_CATEGORIES, world.mix, strict=True):
                cumulative += probability
                if category_draw < cumulative:
                    category = name
                    break
            payments.append(PaymentInput(operation, offset, category, draw('hidden_commit'),
                                         tuple(draw(f'recovery.{i}') for i in range(1, 4)),
                                         tuple(draw(f'abandonment.{i}') for i in range(4))))
    return tuple(payments)


@dataclass(frozen=True, slots=True)
class Deployment:
    command_id: str
    proposal: ChangeProposal
    shipped_tick: int
    event_id: str

    @property
    def ref(self) -> EntityRef:
        return EntityRef('deployment', self.command_id, 1)


@dataclass(frozen=True, slots=True)
class PaymentResult:
    deployment: EntityRef
    operation_id: str
    category: str
    completed: bool
    recovered: bool
    abandoned: bool
    retry_attempts: int
    retry_cost: int
    duplicate_charges: int
    audited_attempts: int
    total_attempts: int
    terminal_latency_ticks: int
    outcome_tick: int
    event_id: str


@dataclass(slots=True)
class _Execution:
    deployment: Deployment
    payment: PaymentInput
    arrival_tick: int
    plan: tuple
    previous_event: str
    committed: bool
    retries: int = 0
    audited: int = 0
    duplicate: int = 0


class PaymentOutcomes:
    """Own the shared queue after delivery is quiescent; dispatch only this owner.

    No automatic ship from green verification, authority/evidence updates, or
    learning. Audit history is private world state; observations are a separate
    available feedback stream. Multiple ships retain their original versions.
    """
    def __init__(self, world: WorldRules, history: EventHistory, clock: SimulationClock) -> None:
        if clock.pending_count:
            raise ValueError('delivery queue must be quiescent before outcomes take ownership')
        self.world, self.history, self.clock = world, history, clock
        self._deployments: tuple[Deployment, ...] = ()
        self._results: tuple[PaymentResult, ...] = ()
        self._observations: tuple[Event, ...] = ()
        self._tasks: dict[str, tuple] = {}
        self._next_task = 0

    @property
    def deployments(self) -> tuple[Deployment, ...]:
        return self._deployments

    @property
    def results(self) -> tuple[PaymentResult, ...]:
        return self._results

    @property
    def observations(self) -> tuple[Event, ...]:
        return self._observations

    def ship(self, proposal: ChangeProposal, workload: tuple[PaymentInput, ...], *, command_id: str) -> Deployment:
        """Preflight pinned provenance and all exposure before appending/scheduling."""
        require_text(command_id, 'command_id')
        if any(d.command_id == command_id for d in self._deployments):
            raise ValueError('duplicate deployment command')
        if type(workload) is not tuple or any(type(p) is not PaymentInput for p in workload):
            raise ValueError('ship requires an immutable workload')
        if len({p.operation_id for p in workload}) != len(workload):
            raise ValueError('duplicate operation in workload')
        if self.history.events and self.history.events[-1].tick > self.clock.now:
            raise ValueError('clock must reach latest fact before shipping')
        events = {e.event_id: e for e in self.history.events}
        source = events.get(proposal.event_id)
        if (source is None or source.event_type != 'ChangeProposalCreated'
            or proposal.ref not in source.entities or proposal.work_item not in source.entities
            or source.tick != proposal.completed_tick
            or source.payload['behavior'] != asdict(proposal.behavior)
            or source.payload['decision_refs'] != [d.ref.as_dict() for d in proposal.decisions]):
            raise ValueError('proposal must match its recorded immutable artifact')
        for decision in proposal.decisions:
            recorded = events.get(decision.event_id)
            # Compare all justification fields, including the original gaps.
            fields = json.loads(json.dumps(asdict(decision)))
            del fields['event_id']
            if (recorded is None or decision.ref not in recorded.entities
                or any(recorded.payload.get(k) != v for k, v in fields.items())):
                raise ValueError('decision must match its recorded provenance')
        ref = EntityRef('deployment', command_id, 1)
        event = self.history.append(
            tick=self.clock.now, event_type='DeploymentCompleted', command_id=command_id,
            correlation_id=command_id, entities=(ref, proposal.ref) + proposal.decision_refs,
            payload={'proposal': proposal.ref.as_dict(), 'behavior': asdict(proposal.behavior),
                     'decision_refs': [d.ref.as_dict() for d in proposal.decisions],
                     'world_id': self.world.world_id, 'model_version': MODEL_VERSION,
                     'workload_operations': [p.operation_id for p in workload]},
            parents=(CausalLink(proposal.event_id, 'direct_cause'),)
                    + tuple(CausalLink(d.event_id, 'direct_cause') for d in proposal.decisions),
        )
        deployment = Deployment(command_id, proposal, self.clock.now, event.event_id)
        self._deployments += (deployment,)
        for payment in workload:
            self._schedule(self.clock.now + payment.arrival_offset, 'arrival', deployment, payment)
        return deployment

    def _schedule(self, tick: int, *task) -> None:
        command = f'outcomes.task.{self._next_task}'
        self._next_task += 1
        self.clock.schedule(tick, command)
        self._tasks[command] = task

    def step(self) -> Event | None:
        # Do not consume earlier work when an external caller has appended future facts.
        self.clock.advance_to(max(self.clock.now, self.history.events[-1].tick if self.history.events else 0))
        scheduled = self.clock.pop_next()
        if scheduled is None:
            return None
        task = self._tasks.pop(scheduled.command_id)
        if task[0] == 'arrival':
            deployment, payment = task[1:]
            committed = payment.category == 'ambiguous' and payment.hidden_commit_draw < self.world.duplicate_probability
            state = _Execution(deployment, payment, self.clock.now,
                               deployment.proposal.behavior.plan(payment.category, payment.operation_id),
                               deployment.event_id, committed)
            self._attempt(state, ordinal=0, succeeded=False, key=payment.operation_id, command=scheduled.command_id)
            if state.plan:
                self._queue_retry(state)
            else:
                self._finish(state, recovered=False, abandoned=not committed and self._abandons(state))
        elif task[0] == 'retry':
            state = task[1]
            ordinal, elapsed, key, _ = state.plan[state.retries]
            state.retries += 1
            stable_ack = state.committed and key == state.payment.operation_id
            probability = self.world.recovery[FAILURE_CATEGORIES.index(state.payment.category)]
            succeeded = stable_ack or (elapsed >= self.world.recovery_delay
                                        and state.payment.recovery_draws[ordinal - 1] < probability)
            if succeeded and not stable_ack:
                state.duplicate = int(state.committed)
                state.committed = True
            attempt = self._attempt(state, ordinal=ordinal, succeeded=succeeded, key=key, command=scheduled.command_id)
            if state.duplicate:
                self._incident(state, attempt)
            abandoned = (not state.committed and state.payment.category.endswith('decline')
                         and not succeeded and self._abandons(state))
            if succeeded or abandoned or state.retries == len(state.plan):
                self._finish(state, recovered=succeeded,
                             abandoned=abandoned or (not state.committed and not succeeded and self._abandons(state)))
            else:
                self._queue_retry(state)
        else:
            deployment, result = task[1:]
            event = self.history.append(
                tick=self.clock.now, event_type='OutcomeObserved', command_id=scheduled.command_id,
                correlation_id=deployment.command_id, entities=(deployment.ref,) + deployment.proposal.decision_refs,
                payload={'deployment': deployment.ref.as_dict(), 'operation_id': result.operation_id,
                         'outcome_tick': result.outcome_tick, 'completed': result.completed,
                         'abandoned': result.abandoned, 'duplicate_charges': result.duplicate_charges,
                         'decision_refs': [d.ref.as_dict() for d in deployment.proposal.decisions]},
                parents=(CausalLink(result.event_id, 'supporting_evidence'),),
            )
            self._observations += (event,)
        return self.history.events[-1]

    def _queue_retry(self, state: _Execution) -> None:
        elapsed = state.plan[state.retries][1]
        self._schedule(state.arrival_tick + elapsed, 'retry', state)

    def _abandons(self, state: _Execution) -> bool:
        return state.payment.abandonment_draws[state.retries] < self.world.abandonment_probability

    def _attempt(self, state: _Execution, *, ordinal: int, succeeded: bool, key: str | None, command: str) -> Event:
        audited = state.deployment.proposal.behavior.audit == 'attempt_lineage'
        state.audited += int(audited)
        event = self.history.append(
            tick=self.clock.now, event_type='PaymentAttempted', command_id=command,
            correlation_id=state.deployment.command_id, entities=(state.deployment.ref,),
            payload={'operation_id': state.payment.operation_id, 'category': state.payment.category,
                     'ordinal': ordinal, 'key': key, 'succeeded': succeeded, 'operation_committed': state.committed,
                     'retry_cost': self.world.retry_cost if ordinal else 0, 'audited': audited},
            parents=(CausalLink(state.previous_event, 'direct_cause'),),
        )
        state.previous_event = event.event_id
        return event

    def _incident(self, state: _Execution, attempt: Event) -> None:
        decision = next(d for d in state.deployment.proposal.decisions if d.decision_id == 'idempotency')
        refs = state.deployment.proposal.decision_refs
        gaps = [e for e in self.history.events if e.event_type == 'AssumptionMade'
                and any(ref in e.entities for ref in refs)]
        self.history.append(
            tick=self.clock.now, event_type='IncidentOccurred', command_id=attempt.command_id + '.incident',
            correlation_id=state.deployment.command_id, entities=(state.deployment.ref, decision.ref),
            payload={'incident_type': 'duplicate_execution', 'operation_id': state.payment.operation_id,
                     'duplicate_charges': 1, 'deployment': state.deployment.ref.as_dict(),
                     'decision': decision.ref.as_dict(),
                     'information_gaps': [{'event_id': e.event_id, **e.payload} for e in gaps]},
            parents=(CausalLink(attempt.event_id, 'direct_cause'),
                     CausalLink(state.deployment.event_id, 'direct_cause'),
                     CausalLink(decision.event_id, 'direct_cause'))
                    + tuple(CausalLink(e.event_id, 'association') for e in gaps),
        )

    def _finish(self, state: _Execution, *, recovered: bool, abandoned: bool) -> None:
        fields = dict(deployment=state.deployment.ref, operation_id=state.payment.operation_id,
                      category=state.payment.category, completed=state.committed, recovered=recovered,
                      abandoned=abandoned, retry_attempts=state.retries,
                      retry_cost=state.retries * self.world.retry_cost, duplicate_charges=state.duplicate,
                      audited_attempts=state.audited, total_attempts=state.retries + 1,
                      terminal_latency_ticks=self.clock.now - state.arrival_tick, outcome_tick=self.clock.now)
        event = self.history.append(
            tick=self.clock.now, event_type='PaymentOutcome', command_id=state.previous_event + '.outcome',
            correlation_id=state.deployment.command_id, entities=(state.deployment.ref,),
            payload={**fields, 'deployment': state.deployment.ref.as_dict()},
            parents=(CausalLink(state.previous_event, 'direct_cause'),),
        )
        result = PaymentResult(**fields, event_id=event.event_id)
        self._results += (result,)
        self._schedule(self.clock.now + self.world.observation_lag, 'observe', state.deployment, result)

    def metrics(self) -> dict:
        """World results over admitted eligible workload; unfinished runs stay pending."""
        eligible = sum(len(e.payload['workload_operations']) for e in self.history.events
                       if e.event_type == 'DeploymentCompleted' and any(d.event_id == e.event_id for d in self._deployments))
        sums = {name: sum(getattr(r, name) for r in self.results) for name in (
            'completed', 'recovered', 'abandoned', 'retry_attempts', 'retry_cost', 'duplicate_charges',
            'audited_attempts', 'total_attempts', 'terminal_latency_ticks')}
        return {**sums, 'eligible': eligible, 'pending': eligible - len(self.results),
                'failed': sum(not r.completed and not r.abandoned for r in self.results),
                'abandonment_rate': sums['abandoned'] / eligible if eligible else None,
                'observed_count': len(self.observations)}
