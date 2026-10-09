"""Immutable delivery artifacts and executable toy retry plans; no generated code.

Plans describe all retries if failures continue. Success/traffic/execution belongs
to the world owner, not this module. Alternative-set and adaptive refinements
must be supplied by a later bounded decision; they are never guessed here.
"""
from dataclasses import dataclass
from typing import Mapping

from .actors import require_text
from .clock import require_tick
from .decisions import DecisionVersion
from .events import EntityRef

FAILURE_CATEGORIES = ('transient', 'soft_decline', 'hard_decline', 'ambiguous')
DECISION_IDS = ('retryable_types', 'retry_count', 'backoff', 'idempotency',
                'declined_handling', 'audit_requirement')


@dataclass(frozen=True, slots=True)
class Goal:
    goal_id: str
    intent: str
    measure: str
    target: float
    observation_window: int
    separate_measures: tuple[str, ...]

    @property
    def ref(self) -> EntityRef:
        return EntityRef('goal', self.goal_id, 1)


@dataclass(frozen=True, slots=True)
class WorkItem:
    work_item_id: str
    goal: EntityRef
    text: str
    required_decisions: tuple[str, ...]

    @property
    def ref(self) -> EntityRef:
        return EntityRef('work_item', self.work_item_id, 1)


@dataclass(frozen=True, slots=True)
class PaymentBehavior:
    """Retry plan v1: ordinal, cumulative delay, operation key, audit mode.

    Capped exponential starts at fixed_delay and doubles each interval to cap.
    Decline handling filters retryable types; it never expands that choice.
    Unspecified idempotency emits None, retaining an explicit unknown key.
    """
    retryable_types: str
    retry_count: int
    backoff: str
    fixed_delay: int
    backoff_cap: int
    declined_handling: str
    idempotency: str
    audit: str

    def __post_init__(self) -> None:
        for name, options in (
            ('retryable_types', ('transient_only', 'all_failures')),
            ('backoff', ('immediate', 'fixed', 'capped_exponential')),
            ('declined_handling', ('do_not_retry', 'soft_only', 'retry_all')),
            ('idempotency', ('stable_key', 'new_key', 'unspecified')),
            ('audit', ('attempt_lineage', 'summary_only', 'no_audit')),
        ):
            if getattr(self, name) not in options:
                raise ValueError(f'{name}: unsupported option; explicit refinement required')
        for name in ('retry_count', 'fixed_delay', 'backoff_cap'):
            require_tick(getattr(self, name))
        if self.retry_count > 3:
            raise ValueError('retry_count exceeds supported finite bound')

    def plan(self, category: str, operation_id: str) -> tuple[tuple[int, int, str | None, str], ...]:
        if category not in FAILURE_CATEGORIES:
            raise ValueError('unknown failure category')
        require_text(operation_id, 'operation_id')
        if self.retryable_types == 'transient_only' and category != 'transient':
            return ()
        if category.endswith('decline') and (
            self.declined_handling == 'do_not_retry'
            or self.declined_handling == 'soft_only' and category == 'hard_decline'
        ):
            return ()
        elapsed, attempts = 0, []
        for ordinal in range(1, self.retry_count + 1):
            if self.backoff == 'fixed':
                elapsed += self.fixed_delay
            elif self.backoff == 'capped_exponential':
                elapsed += min(self.fixed_delay * 2 ** (ordinal - 1), self.backoff_cap)
            key = (operation_id if self.idempotency == 'stable_key' else
                   f'{operation_id}:retry:{ordinal}' if self.idempotency == 'new_key' else None)
            attempts.append((ordinal, elapsed, key, self.audit))
        return tuple(attempts)


def behavior_from_choices(choices: Mapping[str, str], parameters: Mapping[str, int]) -> PaymentBehavior:
    if set(choices) != set(DECISION_IDS):
        raise ValueError('behavior requires exactly all six decisions')
    count = {'none': 'retry.none', 'one': 'retry.one', 'three': 'retry.three'}
    if choices['retry_count'] not in count:
        raise ValueError('adaptive retry requires explicit refinement')
    if choices['retryable_types'] == 'selected_categories':
        raise ValueError('selected categories require explicit refinement')
    if parameters['backoff.immediate'] != 0:
        raise ValueError('immediate backoff requires zero delay')
    return PaymentBehavior(choices['retryable_types'], parameters[count[choices['retry_count']]],
                           choices['backoff'], parameters['backoff.fixed'], parameters['backoff.capped'],
                           choices['declined_handling'], choices['idempotency'], choices['audit_requirement'])


@dataclass(frozen=True, slots=True)
class DeliveryJob:
    command_id: str
    actor_id: str
    work_item: EntityRef
    decisions: tuple[DecisionVersion, ...]
    behavior: PaymentBehavior
    started_tick: int
    completion_tick: int
    resource_cost: int
    event_id: str


@dataclass(frozen=True, slots=True)
class ChangeProposal:
    proposal_id: str
    work_item: EntityRef
    actor_id: str
    decisions: tuple[DecisionVersion, ...]
    behavior: PaymentBehavior
    completed_tick: int
    resource_cost: int
    event_id: str

    @property
    def ref(self) -> EntityRef:
        return EntityRef('change_proposal', self.proposal_id, 1)

    @property
    def decision_refs(self) -> tuple[EntityRef, ...]:
        return tuple(d.ref for d in self.decisions)

    @property
    def unsupported_decisions(self) -> tuple[EntityRef, ...]:
        return tuple(d.ref for d in self.decisions
                     if d.authority_basis in ('inferred_without_authority', 'unresolved', 'conflicted')
                     or d.support != 'supported' or d.missing_information)
