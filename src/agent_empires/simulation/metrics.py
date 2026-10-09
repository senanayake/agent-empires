"""Orthogonal diagnostics over the authoritative audit, never a correctness score."""

from dataclasses import dataclass

from .clock import require_tick
from .events import EventHistory


@dataclass(frozen=True, slots=True)
class DecisionMetrics:
    closure_count: int
    revision_count: int
    assumption_count: int
    authority_grant_count: int
    evidence_backed_information_gain: int


def decision_metrics(history: EventHistory) -> DecisionMetrics:
    """Count closure once per question, and evidence roots once per question.

    evidence_backed_information_gain is a source-coverage diagnostic: distinct
    declared usable/current roots consumed in a world-evidence assessment whose
    lineage does not overlap its subject. Units are (question, source ID) pairs,
    not independent samples, uncertainty reduction, bits or calibrated truth.
    Challenges and inconclusive observations can add coverage. Selection,
    delegation, verification and repeated copies cannot manufacture it. This
    trusted audit projection is not a player-visible knowledge snapshot.
    """
    closed = set()
    sources = set()
    revisions = assumptions = grants = 0
    for event in history.events:
        if event.event_type in ("DecisionSelected", "DecisionRevised"):
            payload = event.payload
            closed.add(payload["decision_id"])
            revisions += event.event_type == "DecisionRevised"
            sources.update((payload["decision_id"], source) for source in payload["backed_source_ids"])
        elif event.event_type == "AssumptionMade":
            assumptions += 1
        elif event.event_type in ("AuthorityGranted", "DecisionDelegated"):
            grants += 1
    return DecisionMetrics(len(closed), revisions, assumptions, grants, len(sources))


def _unit_fraction(value: float) -> None:
    # Range check precedes conversion, including arbitrarily large integers.
    if type(value) not in (int, float) or not 0 <= value <= 1:
        raise ValueError('diagnostic fraction must be finite and in [0, 1]')


def _references(values: tuple[str, ...]) -> None:
    if type(values) is not tuple or any(type(v) is not str or not v.strip() for v in values):
        raise ValueError('references must be an immutable tuple of nonempty IDs')


@dataclass(frozen=True, slots=True)
class AssumptionExposure:
    """Explicit authored diagnostic inputs; not truth or a risk probability.

    ID identifies one assumption version. Impact is conditional severity, not
    exposure likelihood. Uncertainty is unsupported-information fraction, not
    1-confidence. Propagation names downstream artifact versions, never messages
    or payments. Reversibility describes recoverable consequences separately.
    Source roots describe declared dependence, not authenticated independence.
    Resolution preserves accumulated historical age; it does not erase harm.
    """
    assumption_id: str
    uncertainty: float
    impact: float
    propagated_to: tuple[str, ...]
    created_tick: int
    reversibility: float
    source_ids: tuple[str, ...] = ()
    resolved_tick: int | None = None

    def __post_init__(self) -> None:
        if type(self.assumption_id) is not str or not self.assumption_id.strip():
            raise ValueError('assumption ID must identify a nonempty version')
        for value in (self.uncertainty, self.impact, self.reversibility):
            _unit_fraction(value)
        for values in (self.propagated_to, self.source_ids):
            _references(values)
        require_tick(self.created_tick)
        if self.resolved_tick is not None:
            require_tick(self.resolved_tick)
            if self.resolved_tick < self.created_tick:
                raise ValueError('resolution cannot precede creation')


@dataclass(frozen=True, slots=True)
class AssumptionComponents:
    uncertainty: float
    impact: float
    propagation: float
    persistence: float
    reversibility: float

    def __post_init__(self) -> None:
        for value in (self.uncertainty, self.impact, self.propagation,
                      self.persistence, self.reversibility):
            _unit_fraction(value)


def assumption_components(exposure: AssumptionExposure, *, now_tick: int,
                          age_window: int, propagation_limit: int) -> AssumptionComponents:
    """Bound each component in [0,1], with explicit tick/artifact denominators.

    Persistence saturates rather than expiring. Future resolution has no effect
    on an earlier query. Unique artifact counting avoids repeated-path inflation;
    the cap describes a reporting scale, not traffic or incident likelihood.
    """
    if type(exposure) is not AssumptionExposure:
        raise ValueError('expected an AssumptionExposure')
    for value in (now_tick, age_window, propagation_limit):
        require_tick(value)
    if age_window == 0 or propagation_limit == 0:
        raise ValueError('age window and propagation limit must be positive')
    if now_tick < exposure.created_tick:
        raise ValueError('query cannot precede assumption creation')
    end = now_tick if exposure.resolved_tick is None else min(now_tick, exposure.resolved_tick)
    return AssumptionComponents(exposure.uncertainty, exposure.impact,
        min(len(set(exposure.propagated_to)), propagation_limit) / propagation_limit,
        min(end - exposure.created_tick, age_window) / age_window, exposure.reversibility)


def candidate_product(components: AssumptionComponents, *, adjust_reversibility: bool = False) -> float:
    """Optional research index in [0,1]; never a damage rule or probability."""
    if type(components) is not AssumptionComponents or type(adjust_reversibility) is not bool:
        raise ValueError('expected components and an explicit boolean modifier')
    score = (components.impact * components.uncertainty
             * components.propagation * components.persistence)
    return score * (1 - components.reversibility) if adjust_reversibility else score


@dataclass(frozen=True, slots=True)
class AssumptionDebt:
    components: tuple[tuple[str, AssumptionComponents], ...]
    groups: tuple[tuple[str, ...], ...]
    naive_total: float
    grouped_total: float


def assumption_debt(exposures: tuple[AssumptionExposure, ...], *, now_tick: int,
                    age_window: int, propagation_limit: int) -> AssumptionDebt:
    """Compare sum versus max-per-declared-source-group, retaining every vector.

    Group overlap is transitive. Group maxima avoid counting copied claims as
    independent exposure but can undercount distinct harms sharing a source.
    Totals are research indices in [0, number of assumptions/groups], not joint
    probabilities. Missing roots remain separate, not presumed independent.
    No state, clock, history, evidence, authority or world outcome is changed.
    """
    for value in (now_tick, age_window, propagation_limit):
        require_tick(value)
    if not age_window or not propagation_limit:
        raise ValueError('age window and propagation limit must be positive')
    if type(exposures) is not tuple or any(type(e) is not AssumptionExposure for e in exposures):
        raise ValueError('exposures must be an immutable tuple of records')
    records = {}
    for exposure in exposures:
        previous = records.get(exposure.assumption_id)
        if previous is not None and previous != exposure:
            raise ValueError('conflicting duplicate assumption version')
        records[exposure.assumption_id] = exposure
    groups: list[set[str]] = []
    for key in sorted(records):
        group = {key}
        roots = set(records[key].source_ids)
        # Existing groups are disjoint connected components. One new record
        # can bridge several; merge all of them before appending it.
        remaining = []
        for existing in groups:
            existing_roots = {r for member in existing for r in records[member].source_ids}
            if roots & existing_roots:
                group.update(existing)
            else:
                remaining.append(existing)
        groups = remaining + [group]
    vectors = tuple((key, assumption_components(records[key], now_tick=now_tick,
                    age_window=age_window, propagation_limit=propagation_limit)) for key in sorted(records))
    scores = {key: candidate_product(vector) for key, vector in vectors}
    stable_groups = tuple(sorted(tuple(sorted(group)) for group in groups))
    return AssumptionDebt(vectors, stable_groups, sum(scores.values()),
                          sum(max(scores[key] for key in group) for group in stable_groups))
