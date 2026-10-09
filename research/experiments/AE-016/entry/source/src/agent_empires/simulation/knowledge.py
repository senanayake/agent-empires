"""Versioned claims and explicit holdings, without a world-truth oracle.

KnowledgeStore is a trusted simulation owner, never an actor-policy interface.
Give policies only a fresh ActorKnowledge snapshot. Catalog and audit retention
do not grant access; source IDs are opaque provenance, not lookup capabilities.
Python introspection is not a hostile-code security boundary.
"""

from dataclasses import asdict, dataclass, replace
from typing import Iterable

from .actors import Actor, require_text
from .events import CausalLink, EntityRef, Event, EventHistory


def _ids(values: tuple[str, ...], field: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{field} must be an immutable tuple")
    for value in values:
        require_text(value, field)
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate {field}")


@dataclass(frozen=True, slots=True)
class HolderRef:
    kind: str
    holder_id: str

    def __post_init__(self) -> None:
        require_text(self.kind, "holder kind")
        require_text(self.holder_id, "holder_id")
        if self.kind not in ("actor", "artifact"):
            raise ValueError("holder kind must be actor or artifact")


@dataclass(frozen=True, slots=True)
class Artifact:
    """Existing storage with an explicit reader list, empty by default.

    A listed reader must also be present. A document does not give its readers
    personal holdings or broadcast its contents to their teammates.
    """

    artifact_id: str
    reader_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_text(self.artifact_id, "artifact_id")
        _ids(self.reader_ids, "reader_ids")


@dataclass(frozen=True, slots=True)
class KnowledgeItem:
    item_id: str
    version: int
    topic: str
    proposition: str

    def __post_init__(self) -> None:
        EntityRef("knowledge_item", self.item_id, self.version)
        require_text(self.topic, "topic")
        require_text(self.proposition, "proposition")

    @property
    def ref(self) -> EntityRef:
        return EntityRef("knowledge_item", self.item_id, self.version)


@dataclass(frozen=True, slots=True)
class KnowledgeHolding:
    holding_id: str
    item: EntityRef
    holder: HolderRef
    source_ids: tuple[str, ...] = ()
    confidence: str = "unknown"
    freshness: str = "unknown"
    explicit: bool = False
    accessible: bool = True
    version: int = 1

    def __post_init__(self) -> None:
        EntityRef("knowledge_holding", self.holding_id, self.version)
        if type(self.item) is not EntityRef or self.item.entity_type != "knowledge_item":
            raise ValueError("holding item must reference a knowledge_item version")
        if type(self.holder) is not HolderRef:
            raise TypeError("holder must be a HolderRef")
        _ids(self.source_ids, "source_ids")
        if self.confidence not in ("unknown", "low", "medium", "high"):
            raise ValueError("unknown confidence category")
        if self.freshness not in ("unknown", "current", "stale"):
            raise ValueError("unknown freshness category")
        if type(self.explicit) is not bool or type(self.accessible) is not bool:
            raise TypeError("explicit and accessible must be booleans")
        if self.holder.kind == "artifact" and not self.explicit:
            raise ValueError("artifact holdings must be explicit")

    @property
    def ref(self) -> EntityRef:
        return EntityRef("knowledge_holding", self.holding_id, self.version)

    def as_dict(self) -> dict:
        result = asdict(self)
        result["source_ids"] = list(self.source_ids)
        return result


@dataclass(frozen=True, slots=True)
class KnownProposition:
    item: KnowledgeItem
    holding: KnowledgeHolding


@dataclass(frozen=True, slots=True)
class ActorKnowledge:
    """Detached immutable snapshot; refresh after each authoritative command.

    No catalog, audit reference, lazy resolver or privileged store callback is
    included. Old snapshots describe historical access, not current permission.
    """

    actor_id: str
    entries: tuple[KnownProposition, ...]

    def lookup(self, item_id: str, version: int) -> KnowledgeItem | None:
        return next((e.item for e in self.entries
                     if e.item.item_id == item_id and e.item.version == version), None)

    @property
    def source_ids(self) -> tuple[str, ...]:
        """Distinct declared sources, never a count of independent evidence."""
        return tuple(sorted({s for e in self.entries for s in e.holding.source_ids}))

    @property
    def conflicting_topics(self) -> tuple[str, ...]:
        """Syntactic alternatives in the same authored topic, not NLP semantics."""
        claims: dict[str, set[str]] = {}
        for entry in self.entries:
            claims.setdefault(entry.item.topic, set()).add(entry.item.proposition)
        return tuple(sorted(topic for topic, values in claims.items() if len(values) > 1))


class KnowledgeStore:
    """Trusted in-memory holdings owner for one organization.

    Actor holdings are personal; readable artifact holdings are directly usable.
    Stale claims remain available with their label. Team availability means at
    least one present member can read it, not that all members know it. Graph
    routing, transfer costs, truth evaluation and organizational replacement are
    outside this owner. Departure here removes only the actor's knowledge access.
    """

    def __init__(self, history: EventHistory, actors: Iterable[Actor],
                 artifacts: Iterable[Artifact] = ()) -> None:
        self._history = history
        self._actors: dict[str, Actor] = {}
        self._artifacts: dict[str, Artifact] = {}
        for actor in actors:
            if type(actor) is not Actor:
                raise TypeError("expected Actor")
            if actor.actor_id in self._actors:
                raise ValueError("duplicate actor_id")
            self._actors[actor.actor_id] = actor
        for artifact in artifacts:
            if type(artifact) is not Artifact:
                raise TypeError("expected Artifact")
            if artifact.artifact_id in self._artifacts:
                raise ValueError("duplicate artifact_id")
            if not set(artifact.reader_ids) <= self._actors.keys():
                raise ValueError("artifact names an unknown reader")
            self._artifacts[artifact.artifact_id] = artifact
        self._items: dict[EntityRef, KnowledgeItem] = {}
        self._holdings: dict[str, KnowledgeHolding] = {}
        self._departed: frozenset[str] = frozenset()

    def register_item(self, item: KnowledgeItem) -> None:
        """Register private scenario content; this supplies no actor knowledge."""
        if type(item) is not KnowledgeItem:
            raise TypeError("expected KnowledgeItem")
        if item.ref in self._items:
            raise ValueError("item version already exists")
        self._items[item.ref] = item

    def record_holding(self, holding: KnowledgeHolding, *, tick: int,
                       command_id: str, correlation_id: str,
                       parents: tuple[CausalLink, ...] = ()) -> Event:
        """Record an explicitly supplied holding; never inferred from a source ID.

        Trusted setup/delivery code must establish the acquisition. Transfers and
        validation of external source authenticity are not implemented here.
        """
        if type(holding) is not KnowledgeHolding:
            raise TypeError("expected KnowledgeHolding")
        if holding.holding_id in self._holdings or holding.version != 1:
            raise ValueError("new holding must have a new ID and version 1")
        if holding.item not in self._items:
            raise ValueError("unknown item version")
        owner = holding.holder
        if owner.kind == "actor":
            if owner.holder_id not in self._actors or owner.holder_id in self._departed:
                raise ValueError("unknown or departed actor holder")
        elif owner.holder_id not in self._artifacts:
            raise ValueError("unknown artifact holder")
        event = self._history.append(
            tick=tick, event_type="KnowledgeHoldingRecorded", command_id=command_id,
            correlation_id=correlation_id, parents=parents,
            entities=(holding.item, holding.ref),
            payload={"item": asdict(self._items[holding.item]), "holding": holding.as_dict()},
        )
        self._holdings[holding.holding_id] = holding
        return event

    def _readable(self, actor_id: str, holding: KnowledgeHolding,
                  departed: frozenset[str]) -> bool:
        if actor_id in departed or not holding.accessible:
            return False
        if holding.holder.kind == "actor":
            return holding.holder.holder_id == actor_id
        return actor_id in self._artifacts[holding.holder.holder_id].reader_ids

    def view_for(self, actor_id: str) -> ActorKnowledge:
        if actor_id not in self._actors:
            raise ValueError("unknown actor")
        return ActorKnowledge(actor_id, tuple(
            KnownProposition(self._items[h.item], h)
            for _, h in sorted(self._holdings.items())
            if self._readable(actor_id, h, self._departed)
        ))

    def _availability(self, holdings: dict[str, KnowledgeHolding],
                      departed: frozenset[str]) -> dict[str, set[EntityRef]]:
        teams: dict[str, set[EntityRef]] = {a.team_id: set() for a in self._actors.values()}
        for actor in self._actors.values():
            teams[actor.team_id].update(h.item for h in holdings.values()
                                        if self._readable(actor.actor_id, h, departed))
        return teams

    def team_available(self, team_id: str, item: EntityRef) -> bool:
        """Privileged diagnostic, not a team-wide actor snapshot."""
        teams = self._availability(self._holdings, self._departed)
        if team_id not in teams:
            raise ValueError("unknown team")
        return item in teams[team_id]

    def organization_available(self, item: EntityRef) -> bool:
        return any(item in refs for refs in
                   self._availability(self._holdings, self._departed).values())

    def _change_access(self, *, holdings: dict[str, KnowledgeHolding],
                       departed: frozenset[str], tick: int, event_type: str,
                       payload: dict, entities: tuple[EntityRef, ...], command_id: str,
                       correlation_id: str, parents: tuple[CausalLink, ...]) -> tuple[Event, ...]:
        before = self._availability(self._holdings, self._departed)
        after = self._availability(holdings, departed)
        org_before = set().union(*before.values())
        org_after = set().union(*after.values())
        # Stable diagnostic order: organization first, then sorted teams/items.
        losses = [("KnowledgeLost", {"scope": "organization"}, org_before - org_after)]
        losses += [("KnowledgeUnreachable", {"scope": "team", "team_id": team},
                    before[team] - after[team]) for team in sorted(before)]
        # All caller-controlled validation occurs in the first append, before
        # changing state. Remaining facts use validated refs and generated data.
        root = self._history.append(tick=tick, event_type=event_type, payload=payload,
                                    command_id=command_id, correlation_id=correlation_id,
                                    entities=entities, parents=parents)
        self._holdings, self._departed = holdings, departed
        events = [root]
        for kind, scope, refs in losses:
            for ref in sorted(refs, key=lambda r: (r.entity_id, r.version)):
                events.append(self._history.append(
                    tick=tick, event_type=kind, command_id=command_id,
                    correlation_id=correlation_id, entities=(ref,),
                    parents=(CausalLink(root.event_id, "direct_cause"),),
                    payload={**scope, "item_id": ref.entity_id, "version": ref.version},
                ))
        return tuple(events)

    def depart_actor(self, actor_id: str, *, tick: int, command_id: str,
                     correlation_id: str, parents: tuple[CausalLink, ...] = ()) -> tuple[Event, ...]:
        if actor_id not in self._actors or actor_id in self._departed:
            raise ValueError("unknown or already departed actor")
        return self._change_access(
            holdings=self._holdings, departed=self._departed | {actor_id}, tick=tick,
            event_type="ActorDeparted", payload={"actor_id": actor_id},
            entities=(EntityRef("actor", actor_id, 1),), command_id=command_id,
            correlation_id=correlation_id, parents=parents,
        )

    def set_holding_access(self, holding_id: str, accessible: bool, *, tick: int,
                           command_id: str, correlation_id: str,
                           parents: tuple[CausalLink, ...] = ()) -> tuple[Event, ...]:
        if type(accessible) is not bool:
            raise TypeError("accessible must be a boolean")
        if holding_id not in self._holdings:
            raise ValueError("unknown holding")
        old = self._holdings[holding_id]
        new = replace(old, accessible=accessible, version=old.version + 1)
        return self._change_access(
            holdings={**self._holdings, holding_id: new}, departed=self._departed,
            tick=tick, event_type="HoldingAccessChanged",
            payload={"holding": new.as_dict(), "previous_version": old.version},
            entities=(new.item, new.ref), command_id=command_id,
            correlation_id=correlation_id, parents=parents,
        )
