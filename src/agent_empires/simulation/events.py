"""Append-only causal facts and a versioned canonical JSON encoding.

This is an in-memory audit, not an event-sourced state reconstruction mechanism.
"""

from dataclasses import dataclass
import json

from .clock import require_tick


HISTORY_SCHEMA_VERSION = 1
RELATIONS = frozenset({"direct_cause", "supporting_evidence", "association"})


def _text(value: str, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must be nonempty")


def _version(value: int, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer (not bool)")
    if value < 1:
        raise ValueError(f"{field} must be positive")


def canonical_json(value: object) -> bytes:
    """Sorted maps, ordered lists, ASCII escapes, no whitespace or NaN/Infinity.

    Accept only JSON data, rejecting coercions of non-string keys, tuples, sets
    and custom objects. This pinned-runtime format is not an RFC 8785 claim.
    """
    active: set[int] = set()

    def validate(item: object) -> None:
        if item is None or type(item) in (str, bool, int, float):
            return
        if type(item) not in (dict, list):
            raise TypeError("canonical JSON requires JSON values")
        if id(item) in active:
            raise ValueError("cyclic JSON payload")
        active.add(id(item))
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise TypeError("canonical JSON object keys must be strings")
                validate(child)
        else:
            for child in item:
                validate(child)
        active.remove(id(item))

    validate(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_type: str
    entity_id: str
    version: int

    def __post_init__(self) -> None:
        _text(self.entity_type, "entity_type")
        _text(self.entity_id, "entity_id")
        _version(self.version, "entity version")

    def as_dict(self) -> dict:
        return {"entity_type": self.entity_type, "entity_id": self.entity_id,
                "version": self.version}


@dataclass(frozen=True, slots=True)
class CausalLink:
    event_id: str
    relation: str

    def __post_init__(self) -> None:
        _text(self.event_id, "parent event_id")
        _text(self.relation, "relation")
        if self.relation not in RELATIONS:
            raise ValueError(f"unknown causal relation: {self.relation}")

    def as_dict(self) -> dict:
        return {"event_id": self.event_id, "relation": self.relation}


@dataclass(frozen=True, slots=True)
class Event:
    event_id: str
    sequence: int
    tick: int
    event_type: str
    schema_version: int
    command_id: str
    correlation_id: str
    entities: tuple[EntityRef, ...]
    parents: tuple[CausalLink, ...]
    _payload_json: bytes

    @property
    def payload(self) -> dict:
        """A fresh decoded copy; callers cannot mutate stored historical data."""
        return json.loads(self._payload_json)

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id, "sequence": self.sequence, "tick": self.tick,
            "event_type": self.event_type, "schema_version": self.schema_version,
            "command_id": self.command_id, "correlation_id": self.correlation_id,
            "entities": [ref.as_dict() for ref in self.entities],
            "parents": [link.as_dict() for link in self.parents], "payload": self.payload,
        }


class EventHistory:
    """Only successful append assigns an ID; parents must already exist here.

    Entity references are structural: entity existence/access remain domain
    responsibilities. Parent order is supplied explicitly, never from a set.
    """

    def __init__(self, run_id: str) -> None:
        _text(run_id, "run_id")
        self._run_id = run_id
        self._events: list[Event] = []
        self._event_ids: set[str] = set()

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def append(self, *, tick: int, event_type: str, command_id: str,
               correlation_id: str, payload: dict, schema_version: int = 1,
               entities: list[EntityRef] | tuple[EntityRef, ...] = (),
               parents: list[CausalLink] | tuple[CausalLink, ...] = ()) -> Event:
        require_tick(tick)
        if self._events and tick < self._events[-1].tick:
            raise ValueError("fact tick cannot be in the past")
        for field, value in (("event_type", event_type), ("command_id", command_id),
                             ("correlation_id", correlation_id)):
            _text(value, field)
        _version(schema_version, "schema_version")
        for name, refs, kind in (("entities", entities, EntityRef),
                                  ("parents", parents, CausalLink)):
            if type(refs) not in (list, tuple) or any(type(ref) is not kind for ref in refs):
                raise TypeError(f"{name} must be an ordered list/tuple of {kind.__name__}")
        if len(set(parents)) != len(parents):
            raise ValueError("duplicate causal link")
        for link in parents:
            if link.event_id not in self._event_ids:
                raise ValueError(f"expected an earlier parent in this history: {link.event_id}")
        if type(payload) is not dict:
            raise TypeError("event payload must be a JSON object")
        payload_json = canonical_json(payload)
        sequence = len(self._events)
        event = Event(f"{self._run_id}:event:{sequence}", sequence, tick, event_type,
                      schema_version, command_id, correlation_id, tuple(entities),
                      tuple(parents), payload_json)
        self._events.append(event)
        self._event_ids.add(event.event_id)
        return event

    def canonical_bytes(self) -> bytes:
        return canonical_json({"history_schema_version": HISTORY_SCHEMA_VERSION,
                               "run_id": self._run_id,
                               "events": [event.as_dict() for event in self._events]})
