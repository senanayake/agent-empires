"""Orthogonal diagnostics over the authoritative audit, never a correctness score."""

from dataclasses import dataclass

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
