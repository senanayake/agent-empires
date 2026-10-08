from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import random
import runpy
import subprocess
import sys
import time

import pytest

from agent_empires.simulation.events import CausalLink, EntityRef, EventHistory
from agent_empires.simulation.randomness import NamedRandomness


def append(history, **changes):
    args = dict(tick=0, event_type="FixtureRecorded", command_id="command-0",
                correlation_id="correlation-0", payload={"value": 1})
    args.update(changes)
    return history.append(**args)


def test_envelope_ids_sequence_typed_parents_and_entity_versions():
    history = EventHistory("run-17")
    first = append(history)
    second = append(history, tick=3, schema_version=2,
                    entities=[EntityRef("fixture", "subject", 1)],
                    parents=[CausalLink(first.event_id, "direct_cause")])
    third = append(history, tick=3, parents=[
        CausalLink(first.event_id, "supporting_evidence"),
        CausalLink(second.event_id, "association"),
    ])
    assert [e.event_id for e in history.events] == [f"run-17:event:{i}" for i in range(3)]
    assert [e.sequence for e in history.events] == [0, 1, 2]
    assert second.schema_version == 2
    assert second.entities == (EntityRef("fixture", "subject", 1),)
    assert second.parents[0].relation == "direct_cause"
    assert third.parents[1].relation == "association"
    assert second.command_id == "command-0"
    assert second.correlation_id == "correlation-0"


def test_history_is_append_only_including_nested_caller_and_exported_data():
    history = EventHistory("immutable")
    payload = {"nested": [{"value": 3}]}
    entities = [EntityRef("fixture", "item", 1)]
    first = append(history, payload=payload, entities=entities)
    before = history.canonical_bytes()
    snapshot = history.events
    payload["nested"][0]["value"] = 99
    entities.clear()
    first.payload["nested"].clear()
    first.as_dict()["payload"].clear()
    assert history.canonical_bytes() == before
    with pytest.raises(FrozenInstanceError):
        first.tick = 9
    with pytest.raises(AttributeError):
        history.events.append(first)
    with pytest.raises(AttributeError):
        history.run_id = "changed"
    append(history, tick=1)
    assert snapshot == (first,)
    assert len(history.events) == 2


@pytest.mark.parametrize("parent", ["missing", "run:event:1", "run:event:2", "other:event:0"])
def test_dangling_self_future_and_foreign_parents_fail_atomically(parent):
    history = EventHistory("run")
    append(history)
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="earlier parent"):
        append(history, parents=[CausalLink(parent, "direct_cause")])
    assert history.canonical_bytes() == before
    assert append(history).sequence == 1


def test_parent_graph_is_acyclic_by_construction():
    history = EventHistory("dag")
    for i in range(40):
        parents = [CausalLink(e.event_id, "association") for e in history.events[-3:]]
        append(history, tick=i // 4, parents=parents)
    indices = {e.event_id: e.sequence for e in history.events}
    assert all(indices[p.event_id] < e.sequence for e in history.events for p in e.parents)


@pytest.mark.parametrize("changes", [
    {"tick": -1}, {"tick": True}, {"tick": 0.1}, {"tick": "0"},
    {"event_type": ""}, {"event_type": 1}, {"command_id": " "},
    {"correlation_id": None}, {"schema_version": 0}, {"schema_version": True},
    {"parents": ["run:event:0"]}, {"parents": set()}, {"entities": ["item"]},
    {"payload": {"bad": float("nan")}}, {"payload": {"bad": float("inf")}},
    {"payload": {"bad": {1, 2}}}, {"payload": {1: "non-string-key"}},
    {"payload": {"bad": object()}}, {"payload": []},
])
def test_invalid_facts_do_not_append_or_consume_ids(changes):
    history = EventHistory("run")
    before = history.canonical_bytes()
    with pytest.raises((TypeError, ValueError)):
        append(history, **changes)
    assert history.canonical_bytes() == before
    assert append(history).event_id == "run:event:0"


def test_past_facts_duplicate_links_and_cyclic_payload_fail_atomically():
    history = EventHistory("run")
    root = append(history, tick=5)
    link = CausalLink(root.event_id, "direct_cause")
    cycle = {}
    cycle["self"] = cycle
    for changes in ({"tick": 4}, {"tick": 5, "parents": [link, link]},
                    {"tick": 5, "payload": cycle}):
        before = history.canonical_bytes()
        with pytest.raises(ValueError):
            append(history, **changes)
        assert history.canonical_bytes() == before
    assert append(history, tick=5).sequence == 1


def test_invalid_typed_references_are_rejected():
    with pytest.raises(ValueError, match="relation"):
        CausalLink("event", "truth")
    for version in (0, -1, True, "1"):
        with pytest.raises((TypeError, ValueError)):
            EntityRef("fixture", "id", version)
    with pytest.raises(ValueError):
        EventHistory("")


def test_canonical_serialization_sorts_maps_preserves_lists_and_escapes_unicode():
    left, right = EventHistory("canonical"), EventHistory("canonical")
    append(left, payload={"z": {"b": 2, "a": 1}, "a": ["λ", True, None, 1.25]})
    append(right, payload={"a": ["λ", True, None, 1.25], "z": {"a": 1, "b": 2}})
    raw = left.canonical_bytes()
    assert raw == right.canonical_bytes()
    decoded = json.loads(raw)
    assert decoded["history_schema_version"] == 1
    assert decoded["run_id"] == "canonical"
    assert decoded["events"][0]["payload"]["a"] == ["λ", True, None, 1.25]
    assert b"\\u03bb" in raw
    assert raw == json.dumps(decoded, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")


def test_named_streams_repeat_and_isolate_unrelated_draws():
    baseline, varied = NamedRandomness(17), NamedRandomness(17)
    expected = [baseline.stream("world").randrange(10**9) for _ in range(8)]
    for _ in range(100):
        varied.stream("actor/policy").random()
    assert [varied.stream("world").randrange(10**9) for _ in range(8)] == expected
    assert varied.stream("world") is varied.stream("world")
    other = NamedRandomness(23)
    assert [other.stream("world").randrange(10**9) for _ in range(8)] != expected
    shifted = NamedRandomness(17).stream("world")
    shifted.randrange(10**9)
    assert [shifted.randrange(10**9) for _ in range(7)] == expected[1:]


def test_rng_validates_seed_and_stream_identity():
    for seed in (True, 1.0, "17", None):
        with pytest.raises(TypeError, match="seed"):
            NamedRandomness(seed)
    rng = NamedRandomness(-17)
    for name in ("", " ", None, 7):
        with pytest.raises((TypeError, ValueError), match="name"):
            rng.stream(name)
    with pytest.raises(AttributeError):
        rng.root_seed = 0


def load_fixture_runner():
    path = Path(__file__).resolve().parents[2] / "research/experiments/AE-003/replay_fixture.py"
    return runpy.run_path(str(path))


def test_seeded_command_replay_without_wall_clock_or_ambient_randomness(monkeypatch):
    runner = load_fixture_runner()
    fixture = runner["load_fixture"]()

    def forbidden(*args, **kwargs):
        raise AssertionError("ambient time/randomness is forbidden")

    with monkeypatch.context() as blocked:
        for name in ("time", "time_ns", "monotonic", "monotonic_ns", "perf_counter", "sleep"):
            blocked.setattr(time, name, forbidden)
        blocked.setattr(os, "urandom", forbidden)
        for name in ("random", "randrange", "randint", "seed", "getrandbits"):
            blocked.setattr(random, name, forbidden)
        first = runner["replay"](fixture, 17)
        assert runner["replay"](fixture, 17) == first
        assert runner["replay"](fixture, 17, split_advancement=True) == first
        assert runner["replay"](fixture, 17, unrelated_draws=20) == first
        assert runner["replay"](fixture, 23) != first
    events = json.loads(first)["events"]
    assert [event["command_id"] for event in events] == ["cmd-init", "cmd-z", "cmd-a", "cmd-last"]
    assert [event["tick"] for event in events] == [0, 3, 3, 8]


def test_fixture_repeats_across_process_hash_seeds_and_matches_reviewed_evidence():
    runner = load_fixture_runner()
    script = runner["__file__"]
    evidence = Path(script).parent
    for seed in (17, 23):
        outputs = []
        for hash_seed in ("1", "987"):
            env = dict(os.environ, PYTHONHASHSEED=hash_seed)
            process = subprocess.run([sys.executable, script, "--emit-seed", str(seed)],
                                     env=env, capture_output=True, check=True, timeout=30)
            outputs.append(process.stdout)
        expected = runner["replay"](runner["load_fixture"](), seed)
        assert outputs[0] == outputs[1] == expected
        assert (evidence / f"history-seed-{seed}.json").read_bytes() == expected
