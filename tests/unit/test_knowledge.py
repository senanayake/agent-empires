from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
from pathlib import Path
import runpy

import pytest

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.events import CausalLink, EntityRef, EventHistory
from agent_empires.simulation.knowledge import (
    Artifact, HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)


def world(*, readers=("jin",), kinds=("human", "agent")):
    history = EventHistory("knowledge-test")
    actors = [Actor("sarah", kinds[0], "engineering"),
              Actor("jin", kinds[1], "operations")]
    store = KnowledgeStore(history, actors, [Artifact("policy-doc", readers)])
    item = KnowledgeItem("rationale", 1, "declines", "do not retry hard declines")
    store.register_item(item)
    return store, history, item


def hold(store, item, owner="sarah", *, holding_id="h1", kind="actor", **changes):
    holding = KnowledgeHolding(holding_id, item.ref, HolderRef(kind, owner),
                               source_ids=("incident-1",), **changes)
    store.record_holding(holding, tick=0, command_id=f"hold-{holding_id}",
                         correlation_id="fixture")
    return holding


def depart(store, actor="sarah", **changes):
    args = dict(tick=1, command_id=f"depart-{actor}", correlation_id="fixture")
    args.update(changes)
    return store.depart_actor(actor, **args)


def test_sole_tacit_holder_departure_loses_access_but_preserves_audit():
    store, history, item = world()
    holding = hold(store, item)
    earlier = history.events
    earlier_payload = earlier[0].as_dict()
    old_view = store.view_for("sarah")
    events = depart(store)
    assert [e.event_type for e in events] == [
        "ActorDeparted", "KnowledgeLost", "KnowledgeUnreachable"]
    lost = events[1]
    assert lost.entities == (item.ref,)
    assert lost.payload == {"scope": "organization", "item_id": "rationale", "version": 1}
    assert lost.parents == (CausalLink(events[0].event_id, "direct_cause"),)
    assert not store.organization_available(item.ref)
    assert store.view_for("sarah").lookup("rationale", 1) is None
    assert store.view_for("jin").lookup("rationale", 1) is None
    assert history.events[:1] == earlier
    assert earlier[0].as_dict() == earlier_payload
    assert earlier[0].payload["item"]["proposition"] == item.proposition
    assert old_view.lookup("rationale", 1) == item  # snapshot, not current permission
    assert old_view.entries[0].holding == holding
    with pytest.raises(FrozenInstanceError):
        old_view.entries[0].item.proposition = "rewritten"


def test_document_survives_departure_only_for_its_explicit_reader():
    store, history, item = world()
    hold(store, item)
    hold(store, item, "policy-doc", holding_id="doc", kind="artifact", explicit=True)
    assert store.view_for("jin").lookup("rationale", 1) == item
    events = depart(store)
    assert store.organization_available(item.ref)
    assert not store.team_available("engineering", item.ref)
    assert store.team_available("operations", item.ref)
    assert [e.event_type for e in events] == ["ActorDeparted", "KnowledgeUnreachable"]
    assert events[1].payload["team_id"] == "engineering"
    assert not any(e.event_type == "KnowledgeLost" for e in history.events)


def test_document_without_live_readers_does_not_prevent_loss():
    store, _, item = world(readers=("sarah",))
    hold(store, item, "policy-doc", kind="artifact", explicit=True)
    events = depart(store)
    assert any(e.event_type == "KnowledgeLost" for e in events)
    assert not store.organization_available(item.ref)


def test_inaccessible_artifact_and_private_catalog_are_not_answer_keys():
    store, history, item = world(readers=())
    hold(store, item, "policy-doc", kind="artifact", explicit=True)
    private = KnowledgeItem("world-secret", 1, "hidden", "hidden world outcome")
    store.register_item(private)
    for actor in ("sarah", "jin"):
        view = store.view_for(actor)
        assert view.entries == ()
        assert view.lookup(item.item_id, 1) is None
        assert view.lookup(private.item_id, 1) is None
        assert view.lookup("not-in-catalog", 1) is None
        assert not hasattr(view, "history") and not hasattr(view, "register_item")
    assert history.events[0].payload["item"]["proposition"] == item.proposition
    assert not store.organization_available(item.ref)
    assert [e.event_type for e in depart(store)] == ["ActorDeparted"]


def test_membership_does_not_implicitly_copy_another_actors_holding():
    history = EventHistory("same-team")
    store = KnowledgeStore(history, [Actor("a", "human", "t"), Actor("b", "human", "t")])
    item = KnowledgeItem("i", 1, "topic", "claim")
    store.register_item(item)
    hold(store, item, "a")
    assert store.team_available("t", item.ref)
    assert store.view_for("b").entries == ()


def test_redundant_holding_preserves_organization_then_last_departure_loses_it():
    store, _, item = world()
    hold(store, item)
    hold(store, item, "jin", holding_id="h2")
    assert all(e.event_type != "KnowledgeLost" for e in depart(store))
    assert store.view_for("jin").lookup("rationale", 1) == item
    assert sum(e.event_type == "KnowledgeLost" for e in depart(store, "jin", tick=2)) == 1


def test_stale_conflicting_versions_and_confidence_are_not_truth_oracles():
    store, _, old = world()
    newer = KnowledgeItem(old.item_id, 2, old.topic, "retry selected soft declines")
    store.register_item(newer)
    hold(store, old, freshness="stale", confidence="high")
    assert store.view_for("sarah").lookup(old.item_id, 2) is None
    hold(store, newer, holding_id="h2", confidence="low")
    view = store.view_for("sarah")
    assert view.lookup(old.item_id, 1) == old
    assert view.lookup(old.item_id, 2) == newer
    assert view.conflicting_topics == ("declines",)
    assert [entry.holding.confidence for entry in view.entries] == ["high", "low"]
    assert view.entries[0].holding.freshness == "stale"
    assert store.organization_available(old.ref)
    assert len([e for e in depart(store) if e.event_type == "KnowledgeLost"]) == 2


def test_shared_sources_do_not_become_independent_or_grant_hidden_access():
    store, _, item = world()
    hold(store, item, confidence="low")
    hold(store, item, "policy-doc", holding_id="copy", kind="artifact",
         explicit=True, confidence="low")
    assert store.view_for("sarah").source_ids == ("incident-1",)
    view = store.view_for("jin")
    assert view.source_ids == ("incident-1",)
    assert view.entries[0].holding.confidence == "low"
    assert view.lookup("incident-1", 1) is None


def test_multiple_visible_copies_keep_one_declared_source_and_confidence():
    store, _, item = world(readers=("sarah",))
    hold(store, item, confidence="low")
    hold(store, item, holding_id="second-copy", confidence="low")
    hold(store, item, "policy-doc", holding_id="document-copy", kind="artifact",
         explicit=True, confidence="low")
    view = store.view_for("sarah")
    assert len(view.entries) == 3
    assert view.source_ids == ("incident-1",)
    assert all(e.holding.confidence == "low" for e in view.entries)
    assert view.conflicting_topics == ()


def test_access_revocation_emits_loss_once_and_keeps_prior_holding_record():
    store, history, item = world()
    hold(store, item, "policy-doc", kind="artifact", explicit=True)
    original = history.events[0].as_dict()
    events = store.set_holding_access("h1", False, tick=1, command_id="revoke",
                                      correlation_id="fixture")
    assert [e.event_type for e in events] == [
        "HoldingAccessChanged", "KnowledgeLost", "KnowledgeUnreachable"]
    assert store.view_for("jin").entries == ()
    again = store.set_holding_access("h1", False, tick=2, command_id="repeat",
                                     correlation_id="fixture")
    assert not any(e.event_type == "KnowledgeLost" for e in again)
    store.set_holding_access("h1", True, tick=3, command_id="restore",
                             correlation_id="fixture")
    assert store.view_for("jin").lookup(item.item_id, 1) == item
    assert history.events[0].as_dict() == original


@pytest.mark.parametrize("accessible", list(product((False, True), repeat=3)))
def test_three_holder_availability_matches_access_union(accessible):
    store, _, item = world()
    for index, (owner, kind) in enumerate((("sarah", "actor"), ("jin", "actor"),
                                          ("policy-doc", "artifact"))):
        hold(store, item, owner, holding_id=f"h{index}", kind=kind,
             accessible=accessible[index], explicit=kind == "artifact")
    assert store.organization_available(item.ref) == any(accessible)
    events = depart(store)
    assert store.organization_available(item.ref) == any(accessible[1:])
    assert any(e.event_type == "KnowledgeLost" for e in events) == (
        accessible[0] and not any(accessible[1:]))


def test_actor_kind_and_name_relabeling_do_not_change_loss_rules():
    traces = []
    for kinds in (("human", "human"), ("agent", "agent"), ("agent", "human")):
        store, history, item = world(kinds=kinds)
        hold(store, item)
        depart(store)
        traces.append(history.canonical_bytes())
    assert traces[0] == traces[1] == traces[2]
    store, _, item = world()
    hold(store, item, "jin")
    assert all(e.event_type != "KnowledgeLost" for e in depart(store))
    assert any(e.event_type == "KnowledgeLost" for e in depart(store, "jin", tick=2))


def test_arbitrary_actor_names_only_relabel_history():
    traces = []
    for name in ("sarah", "replacement-42"):
        history = EventHistory("relabel")
        store = KnowledgeStore(history, [Actor(name, "agent", "team")])
        item = KnowledgeItem("i", 1, "topic", "claim")
        store.register_item(item)
        hold(store, item, name)
        depart(store, name, command_id="depart")
        traces.append(history.canonical_bytes().replace(name.encode(), b"actor"))
    assert traces[0] == traces[1]


@pytest.mark.parametrize("changes", [
    {"tick": -1}, {"tick": True}, {"tick": 0.5}, {"command_id": ""},
    {"correlation_id": None}, {"parents": (CausalLink("missing", "direct_cause"),)},
])
def test_bad_departure_is_atomic(changes):
    store, history, item = world()
    hold(store, item)
    before = history.canonical_bytes()
    with pytest.raises((TypeError, ValueError)):
        depart(store, **changes)
    assert store.view_for("sarah").lookup(item.item_id, 1) == item
    assert history.canonical_bytes() == before


def test_duplicate_missing_and_departed_references_fail_without_mutation():
    store, history, item = world()
    holding = hold(store, item)
    for bad in (holding, replace(holding, holding_id="missing-item",
                                 item=EntityRef("knowledge_item", "absent", 1)),
                replace(holding, holding_id="missing-holder", holder=HolderRef("actor", "absent"))):
        before = history.canonical_bytes()
        with pytest.raises(ValueError):
            store.record_holding(bad, tick=0, command_id="bad", correlation_id="fixture")
        assert history.canonical_bytes() == before
    with pytest.raises(ValueError):
        store.register_item(replace(item, proposition="overwrite"))
    with pytest.raises(ValueError):
        depart(store, "missing")
    depart(store)
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        depart(store)
    with pytest.raises(ValueError):
        store.record_holding(replace(holding, holding_id="after-departure"),
                             tick=2, command_id="bad", correlation_id="fixture")
    with pytest.raises(ValueError):
        store.view_for("missing")
    assert history.canonical_bytes() == before


def test_rejected_late_recording_and_revocation_preserve_state_and_history():
    store, history, item = world()
    holding = hold(store, item)
    history.append(tick=5, event_type="LaterFact", command_id="advance",
                   correlation_id="fixture", payload={})
    before, view = history.canonical_bytes(), store.view_for("sarah")
    for tick, parents in ((4, ()), (5, (CausalLink("missing", "direct_cause"),))):
        with pytest.raises(ValueError):
            store.record_holding(replace(holding, holding_id="new"), tick=tick,
                                 parents=parents, command_id="bad", correlation_id="fixture")
        with pytest.raises(ValueError):
            store.set_holding_access("h1", False, tick=tick, parents=parents,
                                     command_id="bad", correlation_id="fixture")
        with pytest.raises(ValueError):
            depart(store, tick=tick, parents=parents)
        assert store.view_for("sarah") == view
        assert history.canonical_bytes() == before
    events = store.set_holding_access("h1", False, tick=5,
                                      command_id="valid", correlation_id="fixture")
    assert events[0].sequence == 2
    assert events[0].payload["holding"]["version"] == 2


def test_actor_and_artifact_ids_are_distinct_holder_namespaces():
    history = EventHistory("typed-holders")
    store = KnowledgeStore(history, [Actor("same", "human", "t"), Actor("reader", "agent", "t")],
                           [Artifact("same", ("reader",))])
    item = KnowledgeItem("i", 1, "topic", "claim")
    store.register_item(item)
    hold(store, item, "same", kind="actor")
    assert store.view_for("reader").entries == ()
    hold(store, item, "same", kind="artifact", holding_id="doc", explicit=True)
    assert store.view_for("reader").lookup("i", 1) == item
    assert not any(e.event_type == "KnowledgeLost" for e in depart(store, "same"))


@pytest.mark.parametrize("make", [
    lambda: Actor("", "human", "t"), lambda: Actor("a", "robot", "t"),
    lambda: KnowledgeItem("i", True, "t", "claim"),
    lambda: KnowledgeItem("i", 0, "t", "claim"),
    lambda: HolderRef("scenario", "audit"),
    lambda: Artifact("d", ["a"]),
    lambda: KnowledgeHolding("h", EntityRef("actor", "a", 1), HolderRef("actor", "a")),
    lambda: KnowledgeHolding("h", EntityRef("knowledge_item", "i", 1),
                             HolderRef("actor", "a"), confidence="certain"),
    lambda: KnowledgeHolding("h", EntityRef("knowledge_item", "i", 1),
                             HolderRef("actor", "a"), source_ids=["mutable"]),
    lambda: KnowledgeHolding("h", EntityRef("knowledge_item", "i", 1),
                             HolderRef("actor", "a"), accessible=1),
])
def test_invalid_immutable_records_fail(make):
    with pytest.raises((TypeError, ValueError)):
        make()


def test_artifact_cannot_hold_tacit_information_or_name_unknown_readers():
    store, history, item = world()
    with pytest.raises(ValueError, match="explicit"):
        hold(store, item, "policy-doc", kind="artifact")
    assert history.events == ()
    with pytest.raises(ValueError, match="reader"):
        world(readers=("missing",))


def test_fixture_replays_and_matches_recorded_results():
    path = Path(__file__).resolve().parents[2] / "research/experiments/AE-004"
    runner = runpy.run_path(str(path / "holdings_fixture.py"))
    fixture = json.loads((path / "holdings.json").read_text())
    result, history = runner["replay"](fixture)
    assert (result, history) == runner["replay"](fixture)
    assert (result, history) == runner["replay"](fixture, reverse_registration=True)
    assert json.loads((path / "results.json").read_text()) == result
    assert (path / "history.json").read_bytes() == history
