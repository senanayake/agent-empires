from dataclasses import replace

import pytest

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.communication import Channel, Communication, DistortionRule
from agent_empires.simulation.events import CausalLink, EventHistory
from agent_empires.simulation.knowledge import (
    Artifact, HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)
from agent_empires.simulation.randomness import NamedRandomness


RULE = DistortionRule("declines", "do not retry hard declines", "retry all declines")


def world(*, seed=7, kinds=("human", "agent", "human"), readers=("a",)):
    clock, history, rng = SimulationClock(), EventHistory("channels"), NamedRandomness(seed)
    store = KnowledgeStore(history, [Actor(a, k, "team") for a, k in zip("abc", kinds)],
                           [Artifact("doc", readers)])
    item = KnowledgeItem("policy", 1, RULE.topic, RULE.original)
    store.register_item(item)
    holding = KnowledgeHolding("initial", item.ref, HolderRef("actor", "a"),
                               ("incident-1",), "low", "stale", False)
    store.record_holding(holding, tick=0, command_id="setup", correlation_id="fixture")
    net = Communication(store, clock, history, rng)
    return net, store, clock, history, rng, item


def connect(net, channel=None, **changes):
    channel = channel or Channel("ab", "a", "b", latency=2, capacity=1, transfer_cost=3)
    channel = replace(channel, **changes)
    net.connect(channel, command_id=f"connect-{channel.channel_id}", correlation_id="fixture")
    return channel


def send(net, channel="ab", holding="initial", command="send", **changes):
    args = dict(command_id=command, correlation_id="fixture")
    args.update(changes)
    return net.send(channel, holding, **args)


def drain(net, clock):
    facts = []
    while clock.pending_count:
        facts.extend(net.deliver(clock.pop_next()))
    return facts


def test_control_consumes_capacity_time_and_cost_before_acquisition():
    net, store, clock, history, _, item = world()
    connect(net, connection_cost=2)
    work = send(net)
    sent = history.events[-1]
    assert net.total_cost == 5
    assert store.view_for("b").entries == ()
    with pytest.raises(ValueError, match="capacity"):
        send(net, command="second")
    assert net.total_cost == 5 and clock.pending_count == 1
    clock.advance_to(1)
    assert store.view_for("b").entries == ()
    assert clock.pop_next() == work and clock.now == 2
    events = net.deliver(work)
    assert [e.event_type for e in events] == ["KnowledgeHoldingRecorded", "KnowledgeTransferred"]
    entry, = store.view_for("b").entries
    assert entry.item == item
    assert entry.holding.source_ids == ("incident-1",)
    assert (entry.holding.confidence, entry.holding.freshness, entry.holding.explicit) == (
        "low", "stale", False)
    assert CausalLink(sent.event_id, "direct_cause") in events[0].parents
    assert CausalLink(events[0].event_id, "direct_cause") in events[1].parents
    assert events[1].payload["source_holding"]["entity_id"] == "initial"
    assert sent.payload["delivery_tick"] == 2
    assert store.view_for("a").lookup("policy", 1) == item


def test_full_loss_has_no_delivery_or_distortion_but_is_charged():
    net, store, clock, history, _, _ = world()
    connect(net, loss_probability=1, distortion_probability=1, distortion=RULE)
    send(net)
    events = drain(net, clock)
    assert [e.event_type for e in events] == ["InformationLost"]
    assert events[0].payload["reason"] == "channel_loss"
    assert events[0].tick == 2 and net.total_cost == 3
    assert not store.view_for("b").entries
    assert not any(e.event_type == "InformationDistorted" for e in history.events)


def test_distortion_is_a_new_claim_with_original_lineage_and_unchanged_audit():
    net, store, clock, history, _, item = world()
    connect(net, distortion_probability=1, distortion=RULE)
    original = history.events[0].as_dict()
    send(net)
    events = drain(net, clock)
    assert [e.event_type for e in events] == [
        "KnowledgeHoldingRecorded", "InformationDistorted", "KnowledgeTransferred"]
    altered, = store.view_for("b").entries
    assert altered.item.proposition == RULE.alternative
    assert altered.item.topic == item.topic and altered.item.ref != item.ref
    assert altered.holding.source_ids == ("incident-1",)
    assert altered.holding.confidence == "low"
    assert altered.holding.freshness == "stale"
    assert store.view_for("b").lookup("policy", 1) is None
    assert store.view_for("a").lookup("policy", 1) == item
    assert history.events[0].as_dict() == original
    assert events[1].payload["original_item"] == item.ref.as_dict()
    assert CausalLink(events[1].event_id, "direct_cause") in events[2].parents


def test_capacity_resets_each_tick_and_edges_are_independent():
    net, store, clock, history, _, _ = world()
    connect(net, capacity=2)
    connect(net, Channel("ac", "a", "c", latency=3, capacity=1))
    send(net, command="one")
    send(net, command="two")
    send(net, "ac", command="other-edge")
    with pytest.raises(ValueError, match="capacity"):
        send(net, command="overflow")
    clock.advance_to(1)
    send(net, command="next-tick")
    drain(net, clock)
    delivered = [e.tick for e in history.events if e.event_type == "KnowledgeTransferred"]
    assert delivered == [2, 2, 3, 3]
    assert len(store.view_for("b").entries) == 3


def test_disconnected_reverse_and_automatic_multihop_access_are_absent():
    net, store, clock, history, _, _ = world()
    connect(net)
    connect(net, Channel("bc", "b", "c", latency=2, capacity=1))
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="channel"):
        send(net, "ba")
    with pytest.raises(ValueError, match="accessible"):
        send(net, "bc")
    assert history.canonical_bytes() == before
    send(net)
    drain(net, clock)
    assert store.view_for("c").entries == ()
    forwarded = store.view_for("b").entries[0].holding.holding_id
    send(net, "bc", forwarded, "forward")
    drain(net, clock)
    assert clock.now == 4 and store.view_for("c").source_ids == ("incident-1",)


def test_duplicate_source_over_two_routes_never_adds_independent_support():
    net, store, clock, _, _, _ = world()
    for edge in (Channel("ab", "a", "b", 1, 1), Channel("ac", "a", "c", 1, 1),
                 Channel("bc", "b", "c", 1, 1)):
        connect(net, edge)
    send(net, command="via-b")
    send(net, "ac", command="direct")
    drain(net, clock)
    send(net, "bc", store.view_for("b").entries[0].holding.holding_id, "forward")
    drain(net, clock)
    view = store.view_for("c")
    assert len(view.entries) == 2 and view.source_ids == ("incident-1",)
    assert all(e.holding.confidence == "low" for e in view.entries)


def test_repeated_sends_cite_acquisition_not_an_unrelated_previous_send():
    net, _, _, history, _, _ = world()
    connect(net, capacity=2)
    source_fact, connected = history.events
    send(net, command="one")
    first = history.events[-1]
    send(net, command="two")
    second = history.events[-1]
    assert second.parents == (CausalLink(source_fact.event_id, "direct_cause"),
                              CausalLink(connected.event_id, "direct_cause"))
    assert all(link.event_id != first.event_id for link in second.parents)


def test_external_work_and_equal_time_deliveries_share_clock_without_being_swallowed():
    net, store, clock, history, _, _ = world()
    connect(net)
    external = clock.schedule(2, "outside-command")
    transfer = send(net)
    assert clock.pop_next() == external
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        net.deliver(external)
    assert history.canonical_bytes() == before
    assert clock.pop_next() == transfer
    net.deliver(transfer)
    assert len(store.view_for("b").entries) == 1


def test_hidden_document_cannot_be_sent_and_revocation_does_not_recall_admitted_snapshot():
    net, store, clock, history, _, item = world(readers=())
    connect(net)
    holding = KnowledgeHolding("sealed", item.ref, HolderRef("artifact", "doc"), explicit=True)
    store.record_holding(holding, tick=0, command_id="sealed", correlation_id="fixture")
    with pytest.raises(ValueError, match="accessible"):
        send(net, holding="sealed")
    send(net)
    clock.advance_to(1)
    store.set_holding_access("initial", False, tick=1, command_id="revoke", correlation_id="fixture")
    drain(net, clock)
    assert store.view_for("b").lookup("policy", 1) == item
    assert store.view_for("a").entries == ()


def test_bad_history_time_and_bad_connect_parents_are_atomic():
    net, _, clock, history, _, _ = world()
    channel = Channel("ab", "a", "b", 1, 1, connection_cost=9)
    with pytest.raises(ValueError):
        net.connect(channel, command_id="connect", correlation_id="fixture",
                    parents=(CausalLink("missing", "direct_cause"),))
    assert net.total_cost == 0
    connect(net, channel)
    history.append(tick=1, event_type="External", command_id="external",
                   correlation_id="fixture", payload={})
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="past"):
        send(net)
    assert history.canonical_bytes() == before and clock.pending_count == 0
    assert net.total_cost == 9


def test_only_current_accessible_holdings_can_be_sent_including_readable_artifacts():
    net, store, clock, history, _, item = world()
    connect(net)
    doc = KnowledgeHolding("doc-h", item.ref, HolderRef("artifact", "doc"),
                           ("incident-1",), explicit=True)
    store.record_holding(doc, tick=0, command_id="doc", correlation_id="fixture")
    store.set_holding_access("initial", False, tick=0, command_id="revoke", correlation_id="fixture")
    for unavailable in ("initial", "policy", "incident-1", "private", "missing"):
        before = history.canonical_bytes()
        with pytest.raises(ValueError, match="accessible"):
            send(net, holding=unavailable)
        assert history.canonical_bytes() == before
    send(net, holding="doc-h")
    drain(net, clock)
    assert store.view_for("b").entries[0].holding.explicit


@pytest.mark.parametrize("actor,delivered", [("a", True), ("b", False)])
def test_inflight_snapshot_survives_sender_departure_but_cannot_reach_departed_recipient(actor, delivered):
    net, store, clock, _, _, item = world()
    connect(net)
    send(net)
    clock.advance_to(1)
    store.depart_actor(actor, tick=clock.now, command_id="depart", correlation_id="fixture")
    events = drain(net, clock)
    assert (store.view_for("b").lookup("policy", 1) == item) == delivered
    assert events[-1].event_type == ("KnowledgeTransferred" if delivered else "InformationLost")
    if not delivered:
        assert events[-1].payload["reason"] == "recipient_unavailable"


def replay(seed, *, kinds=("human", "agent", "human"), trust=0.5, extra_draw=False):
    net, store, clock, history, rng, _ = world(seed=seed, kinds=kinds)
    connect(net, capacity=4, loss_probability=0.25, distortion_probability=0.5,
            distortion=RULE, trust=trust)
    if extra_draw:
        for _ in range(30):
            rng.stream("world").random()
    for i in range(4):
        send(net, command=f"message-{i}")
    drain(net, clock)
    return history, store


def test_seeded_replay_and_unrelated_randomness_and_actor_kind_controls():
    outcomes = set()
    for seed in range(32):
        history, _ = replay(seed)
        assert history.canonical_bytes() == replay(seed)[0].canonical_bytes()
        assert history.canonical_bytes() == replay(seed, extra_draw=True)[0].canonical_bytes()
        assert history.canonical_bytes() == replay(seed, kinds=("agent",) * 3)[0].canonical_bytes()
        outcomes.add(tuple(e.event_type for e in history.events))
    assert len(outcomes) > 1


def test_trust_is_metadata_without_confidence_or_reliability_effects():
    lo, lo_store = replay(4, trust=0)
    hi, hi_store = replay(4, trust=1)
    assert lo_store.view_for("b") == hi_store.view_for("b")
    assert [(e.tick, e.event_type) for e in lo.events] == [(e.tick, e.event_type) for e in hi.events]


@pytest.mark.parametrize("changes", [
    {"command_id": ""}, {"correlation_id": None},
    {"parents": (CausalLink("absent", "direct_cause"),)},
])
def test_invalid_send_is_atomic_and_does_not_consume_capacity_or_rng(changes):
    net, store, clock, history, _, _ = world()
    connect(net, distortion_probability=1, distortion=RULE)
    before = history.canonical_bytes()
    with pytest.raises((TypeError, ValueError)):
        send(net, **changes)
    assert net.total_cost == 0 and clock.pending_count == 0
    assert history.canonical_bytes() == before
    send(net)
    drain(net, clock)
    assert store.view_for("b").entries[0].item.proposition == RULE.alternative


def test_duplicate_send_early_unknown_and_duplicate_delivery_do_not_mutate():
    net, store, clock, history, _, _ = world()
    connect(net, capacity=2)
    work = send(net)
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        send(net)
    with pytest.raises(ValueError):
        net.deliver(work)
    assert history.canonical_bytes() == before and net.total_cost == 3
    assert clock.pop_next() == work
    net.deliver(work)
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        net.deliver(work)
    with pytest.raises(ValueError):
        net.deliver(replace(work, command_id="unknown"))
    assert history.canonical_bytes() == before and len(store.view_for("b").entries) == 1


@pytest.mark.parametrize("changes", [
    {"latency": 0}, {"latency": True}, {"latency": 1.5}, {"capacity": 0},
    {"capacity": -1}, {"capacity": True}, {"transfer_cost": -1}, {"connection_cost": 0.5},
    {"loss_probability": -0.1}, {"loss_probability": 1.1}, {"loss_probability": float("nan")},
    {"distortion_probability": float("inf")}, {"trust": True}, {"trust": -1},
    {"channel_id": ""}, {"recipient": "a"}, {"distortion_probability": 1},
])
def test_invalid_channel_parameters_are_rejected(changes):
    with pytest.raises((TypeError, ValueError)):
        replace(Channel("ab", "a", "b", 1, 1), **changes)


def test_invalid_or_nonchanging_distortion_rule_is_rejected():
    with pytest.raises(ValueError):
        DistortionRule("topic", "same", "same")
    net, _, clock, history, _, _ = world()
    connect(net, distortion_probability=1, distortion=DistortionRule("other", "x", "y"))
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="distortion"):
        send(net)
    assert history.canonical_bytes() == before and clock.pending_count == 0


def test_unknown_departed_and_duplicate_channel_endpoints_fail_atomically():
    net, store, _, history, _, _ = world()
    connect(net, connection_cost=2)
    for edge in (Channel("ab", "a", "b", 1, 1), Channel("ax", "a", "missing", 1, 1)):
        before = history.canonical_bytes()
        with pytest.raises(ValueError):
            connect(net, edge)
        assert history.canonical_bytes() == before and net.total_cost == 2
    store.depart_actor("b", tick=0, command_id="depart", correlation_id="fixture")
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        send(net)
    assert history.canonical_bytes() == before


def test_fast_route_and_cheap_route_are_useful_under_different_constraints():
    results = []
    for direct in (True, False):
        net, store, clock, _, _, _ = world()
        if direct:
            connect(net, Channel("ac", "a", "c", 1, 1, connection_cost=6, transfer_cost=4))
            send(net, "ac")
        else:
            for edge in (Channel("ab", "a", "b", 2, 1, connection_cost=1, transfer_cost=1),
                         Channel("bc", "b", "c", 2, 1, connection_cost=1, transfer_cost=1)):
                connect(net, edge)
            send(net)
            drain(net, clock)
            send(net, "bc", store.view_for("b").entries[0].holding.holding_id, "forward")
        drain(net, clock)
        assert store.view_for("c").source_ids == ("incident-1",)
        results.append((clock.now, net.total_cost))
    assert results == [(1, 10), (4, 4)]


def ancestor_ids(history, event):
    by_id = {e.event_id: e for e in history.events}
    pending = [p.event_id for p in event.parents]
    found = set()
    while pending:
        event_id = pending.pop()
        if event_id not in found:
            found.add(event_id)
            pending.extend(p.event_id for p in by_id[event_id].parents)
    return found


def test_forwarding_preserves_the_distortion_in_its_causal_ancestry():
    net, store, clock, history, _, _ = world()
    connect(net, distortion_probability=1, distortion=RULE)
    connect(net, Channel('bc', 'b', 'c', latency=1, capacity=1))
    send(net)
    drain(net, clock)
    distortion = next(e for e in history.events if e.event_type == 'InformationDistorted')
    holding = store.view_for('b').entries[0].holding.holding_id
    send(net, 'bc', holding, 'forward-distorted')
    assert distortion.event_id in ancestor_ids(history, history.events[-1])


def test_access_restoration_preserves_original_acquisition_ancestry():
    net, store, _, history, _, _ = world()
    acquisition = history.events[0]
    connect(net)
    store.set_holding_access('initial', False, tick=0, command_id='revoke', correlation_id='fixture')
    store.set_holding_access('initial', True, tick=0, command_id='restore', correlation_id='fixture')
    send(net)
    assert acquisition.event_id in ancestor_ids(history, history.events[-1])


def test_unavailable_recipient_loss_cites_the_departure_cause():
    net, store, clock, history, _, _ = world()
    connect(net)
    send(net)
    clock.advance_to(1)
    departure = store.depart_actor('b', tick=1, command_id='depart', correlation_id='fixture')[0]
    events = drain(net, clock)
    lost = events[-1]
    assert lost.payload['reason'] == 'recipient_unavailable'
    assert CausalLink(departure.event_id, 'direct_cause') in lost.parents
