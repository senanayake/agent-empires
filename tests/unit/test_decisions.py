from dataclasses import FrozenInstanceError, replace

import pytest

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.communication import Channel, Communication, DistortionRule
from agent_empires.simulation.decisions import (
    AuthorityGrant, AuthorityRegistry, CapabilityProfile, DecisionQuestion,
    Decisions, EvidenceUse,
)
from agent_empires.simulation.events import CausalLink, EntityRef, EventHistory
from agent_empires.simulation.knowledge import (
    HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)
from agent_empires.simulation.metrics import decision_metrics
from agent_empires.simulation.randomness import NamedRandomness


def world(kind="agent", options=("none", "one", "three"), topic="retry_count"):
    history = EventHistory("decisions")
    store = KnowledgeStore(history, [Actor("a", kind, "team"), Actor("owner", "human", "team")])
    authority = AuthorityRegistry(store, history)
    decisions = Decisions(store, authority, history)
    question = DecisionQuestion("d", topic, "WI", options)
    decisions.register(question)
    return decisions, authority, store, history, question


def select(decisions, option="one", **changes):
    args = dict(actor_id="a", expected_version=0, tick=0, command_id="select",
                correlation_id="case", confidence="high", reason="authored choice")
    args.update(changes)
    return decisions.select("d", option, **args)


def claim(store, item_id, proposition, roots, *, actor="a", topic="retry_count",
          freshness="current", tick=0):
    item = KnowledgeItem(item_id, 1, topic, proposition)
    store.register_item(item)
    store.record_holding(KnowledgeHolding(item_id, item.ref, HolderRef("actor", actor),
                                         roots, "high", freshness), tick=tick,
                         command_id=f"hold-{item_id}", correlation_id="case")
    return item


def grant(authority, grant_id="root", actor="owner", options=("none", "one", "three"), **changes):
    args = dict(grant_id=grant_id, actor_id=actor, scope="WI", options=options,
                can_delegate=True)
    args.update(changes)
    result = AuthorityGrant(**args)
    authority.add_root(result, tick=0, command_id=f"grant-{grant_id}", correlation_id="case")
    return result


def evidence(holding, subject, option="one", **changes):
    args = dict(holding_id=holding, subject=subject, option=option,
                stance="supports", method="observation", quality="usable")
    args.update(changes)
    return EvidenceUse(**args)


def test_t1_inferred_green_tests_do_not_validate_their_source_then_new_evidence_arrives():
    d, auth, store, history, q = world(options=("stable", "new"), topic="idempotency")
    hidden = claim(store, "contract", "stable", ("interface",), actor="owner", topic=q.topic)
    profile = CapabilityProfile(("new", "stable"), confidence="high")
    before = store.view_for("a")
    v1 = d.infer("d", "a", profile, expected_version=0, tick=0,
                 command_id="infer", correlation_id="case", missing_information=("interface rationale",))
    assert v1.selected == "new" and v1.confidence == "high"
    assert v1.authority_basis == "inferred_without_authority" and v1.support == "none"
    assert store.view_for("a") == before and before.lookup(hidden.item_id, 1) is None
    assert [e.event_type for e in history.events][-2:] == ["DecisionSelected", "AssumptionMade"]
    assert history.events[-1].payload["missing_information"] == ["interface rationale"]
    assert decision_metrics(history).closure_count == 1
    assert decision_metrics(history).evidence_backed_information_gain == 0
    claim(store, "green", "passes chosen spec", v1.source_ids, topic=q.topic)
    v2 = select(d, "new", expected_version=1, command_id="green", evidence=(
        evidence("green", v1.ref, "new", method="verification"),))
    assert v2.support == "weak" and decision_metrics(history).evidence_backed_information_gain == 0
    claim(store, "duplicate-observation", "duplicate observed", ("monitor",), topic=q.topic)
    grant(auth, actor="a", options=q.alternatives)
    v3 = select(d, "stable", expected_version=2, command_id="revise", grant_id="root", evidence=(
        evidence("duplicate-observation", v1.ref, "new", stance="challenges"),))
    assert v3.authority_basis == "explicit_authorization"
    assert v3.support == "inconclusive"  # ruling out new does not prove stable
    assert d.version("d", 1) == v1 and v1.selected == "new"
    assert decision_metrics(history).closure_count == 1
    assert decision_metrics(history).evidence_backed_information_gain == 1


def test_t2_delegation_and_revocation_change_permission_without_world_knowledge():
    d, auth, store, history, _ = world()
    grant(auth)
    before = store.view_for("a")
    auth.delegate("child", "root", "owner", "a", options=("none", "one"), tick=0,
                  command_id="delegate", correlation_id="case")
    assert store.view_for("a") == before
    v1 = select(d, grant_id="child")
    assert v1.authority_basis == "delegated_discretion" and v1.support == "none"
    auth.revoke("child", tick=1, command_id="revoke", correlation_id="case")
    with pytest.raises(ValueError, match="authority"):
        select(d, grant_id="child", expected_version=1, tick=1)
    v2 = select(d, expected_version=1, tick=1, command_id="unsupported")
    assert v2.authority_basis == "inferred_without_authority"
    assert v1.authority_basis == "delegated_discretion" and v1.grant_ref.version == 1
    assert store.view_for("a") == before
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_t3_authorized_policy_can_be_challenged_and_old_version_stays_pinned():
    d, auth, store, history, q = world(options=("no_declines", "soft", "all"), topic="declines")
    grant(auth, actor="a", options=("no_declines",), basis="policy_constraint")
    v1 = select(d, "no_declines", grant_id="root")
    deployed_ref = v1.ref  # a consumer's pin, not an implemented deployment engine
    claim(store, "trial", "authored matched soft-decline recovery", ("trial-observation",), topic=q.topic)
    obs = evidence("trial", v1.ref, "no_declines", stance="challenges")
    v2 = select(d, "no_declines", grant_id="root", expected_version=1, command_id="challenge", evidence=(obs,))
    assert v2.support == "challenged" and v2.authority_basis == "policy_constraint"
    assert v2.confidence == "high"  # no implicit confidence/belief revision
    # An explicit authored policy lifecycle input is needed before selecting soft.
    # This is not a belief/goal/policy-enactment engine.
    with pytest.raises(ValueError):
        select(d, "soft", grant_id="root", expected_version=2, evidence=(obs,))
    auth.revoke("root", tick=0, command_id="retire-policy", correlation_id="case")
    grant(auth, "policy2", actor="a", options=("soft",), basis="policy_constraint")
    v3 = select(d, "soft", grant_id="policy2", expected_version=2, command_id="revision", confidence="low", evidence=(obs,))
    assert v3.selected == "soft" and d.version("d", deployed_ref.version) == v1
    assert decision_metrics(history).evidence_backed_information_gain == 1
    assert not any(e.event_type in ("BeliefRevised", "PolicyRevised") for e in history.events)


def test_t4_copied_reports_add_one_source_and_independent_conflict_survives_revision():
    d, auth, store, history, q = world(options=("stable", "new"), topic="idempotency")
    grant(auth, actor="a", options=q.alternatives)
    for name in ("report1", "report2"):
        claim(store, name, "new", ("vendor",), topic=q.topic)
    refs = tuple(evidence(name, q.ref, "new", method="report") for name in ("report1", "report2"))
    v1 = select(d, "new", grant_id="root", evidence=refs)
    assert v1.support == "supported"
    assert v1.backed_source_ids == ("vendor",)
    claim(store, "trace", "new keys duplicate", ("monitor",), topic=q.topic)
    refs += (evidence("trace", v1.ref, "new", stance="challenges"),)
    v2 = select(d, "new", expected_version=1, grant_id="root", command_id="conflict", evidence=refs)
    assert v2.support == "conflicted" and v2.confidence == "high"
    v3 = select(d, "stable", expected_version=2, grant_id="root", command_id="caution", confidence="low", evidence=refs)
    assert v3.support == "conflicted" and v3.confidence == "low"
    assert decision_metrics(history).evidence_backed_information_gain == 2


def test_t5_benign_observation_is_inconclusive_and_cannot_repair_missing_authority():
    d, _, store, history, _ = world()
    v1 = select(d, "three")
    claim(store, "window", "all sampled payments recovered on first retry", ("window-1",))
    v2 = select(d, "three", expected_version=1, command_id="limited-window", evidence=(
        evidence("window", v1.ref, "three", stance="inconclusive"),))
    assert v2.selected == v1.selected and v2.support == "inconclusive"
    assert v2.authority_basis == "inferred_without_authority"
    assert decision_metrics(history).closure_count == 1
    assert decision_metrics(history).evidence_backed_information_gain == 1
    assert not any(e.event_type == "IncidentOccurred" for e in history.events)


@pytest.mark.parametrize("option,changes", [("four", {}), ("one", {"expected_version":1}),
    ("one", {"confidence":0.99}), ("one", {"reason":""}),
    ("one", {"parents":(CausalLink("missing", "direct_cause"),)})])
def test_bad_selection_leaves_no_partial_version_history_or_metrics(option, changes):
    d, _, _, history, _ = world()
    before = history.canonical_bytes()
    with pytest.raises((ValueError, TypeError)):
        select(d, option, **changes)
    assert history.canonical_bytes() == before
    assert d.versions("d") == () and decision_metrics(history).closure_count == 0


@pytest.mark.parametrize("changes", [{"actor_id":"owner"}, {"scope":"other"},
    {"options":("none",)}, {"action":"deploy"}, {"valid_from":1}, {"valid_until":1}])
def test_authority_cannot_be_used_by_wrong_actor_scope_option_action_or_time(changes):
    d, auth, _, history, _ = world()
    grant(auth, actor=changes.get("actor_id", "a"),
          **{key: value for key, value in changes.items() if key != "actor_id"})
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="authority"):
        select(d, grant_id="root", tick=1 if "valid_until" in changes else 0)
    assert history.canonical_bytes() == before


def test_delegation_cannot_widen_or_outlive_parent_and_revocation_cascades():
    d, auth, _, history, _ = world()
    grant(auth, options=("none", "one"), valid_until=3)
    for options in [("three",), ()]:
        with pytest.raises(ValueError):
            auth.delegate("bad", "root", "owner", "a", options=options, tick=0,
                          command_id="bad", correlation_id="case")
    with pytest.raises(ValueError):
        auth.delegate("bad", "root", "a", "a", options=("one",), tick=0,
                      command_id="bad", correlation_id="case")
    auth.delegate("child", "root", "owner", "a", options=("one",), tick=0,
                  command_id="delegate", correlation_id="case")
    select(d, grant_id="child")
    auth.revoke("root", tick=1, command_id="revoke-root", correlation_id="case")
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        select(d, grant_id="child", expected_version=1, tick=1)
    assert history.canonical_bytes() == before


def test_non_delegable_root_rejects_delegation():
    _, auth, _, history, _ = world()
    grant(auth, can_delegate=False)
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        auth.delegate("child", "root", "owner", "a", options=("one",), tick=0,
                      command_id="delegate", correlation_id="case")
    assert history.canonical_bytes() == before


@pytest.mark.parametrize("bad_subject", [EntityRef("decision", "missing", 1),
    EntityRef("decision", "d", 1), EntityRef("decision_question", "d", 2)])
def test_unknown_future_or_wrong_subject_evidence_is_rejected(bad_subject):
    d, _, store, history, _ = world()
    claim(store, "report", "one", ("monitor",))
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        select(d, evidence=(evidence("report", bad_subject),))
    assert history.canonical_bytes() == before


@pytest.mark.parametrize("access", ["hidden", "revoked", "departed"])
def test_access_is_refreshed_and_private_evidence_is_rejected(access):
    d, _, store, history, q = world()
    claim(store, "report", "one", ("monitor",), actor="owner" if access=="hidden" else "a")
    if access == "revoked":
        store.set_holding_access("report", False, tick=0, command_id="revoke", correlation_id="case")
    elif access == "departed":
        store.depart_actor("a", tick=0, command_id="depart", correlation_id="case")
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        select(d, evidence=(evidence("report", q.ref),))
    assert history.canonical_bytes() == before


@pytest.mark.parametrize("roots,freshness,quality", [((), "current", "usable"),
    (("source",), "stale", "usable"), (("source",), "unknown", "usable"),
    (("source",), "current", "weak")])
def test_weak_unknown_or_stale_provenance_allows_high_confidence_without_gain(roots, freshness, quality):
    d, _, store, history, q = world()
    claim(store, "report", "one", roots, freshness=freshness)
    v = select(d, evidence=(evidence("report", q.ref, quality=quality),))
    assert v.confidence == "high" and v.support == "weak"
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_shared_selection_source_cannot_validate_itself_even_with_new_report_id():
    d, _, store, history, q = world()
    claim(store, "interpretation", "one", ("spec",))
    v1 = select(d, rationale_holding_ids=("interpretation",))
    claim(store, "copied-test", "one", ("spec", "derived-check"))
    v2 = select(d, expected_version=1, command_id="copy", evidence=(
        evidence("copied-test", v1.ref, method="report"),))
    assert v2.support == "weak" and not v2.backed_source_ids
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_matched_profiles_ignore_actor_kind_and_duplicate_claim_votes():
    traces = []
    for kind in ("human", "agent"):
        d, _, store, history, _ = world(kind)
        claim(store, "first", "one", ("shared",))
        for i in range(5):
            claim(store, f"copy{i}", "three", ("other",))
        profile = CapabilityProfile(("one", "three", "none"), confidence="low")
        v = d.infer("d", "a", profile, expected_version=0, tick=0, command_id="infer", correlation_id="case")
        assert v.selected == "one" and v.support == "none"
        traces.append(history.canonical_bytes())
    assert traces[0] == traces[1]


def test_profile_changes_behavior_and_disabled_inference_is_atomic():
    d, _, store, history, _ = world()
    claim(store, "claim", "one", ("note",))
    profile = CapabilityProfile(("three", "one", "none"), read_claims=False)
    assert d.infer("d", "a", profile, expected_version=0, tick=0, command_id="infer", correlation_id="case").selected == "three"
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        d.infer("d", "a", replace(profile, can_infer=False), expected_version=1, tick=0,
                command_id="disabled", correlation_id="case")
    assert history.canonical_bytes() == before


def test_historical_versions_and_detached_payloads_are_immutable():
    d, _, _, history, _ = world()
    v1 = select(d)
    v2 = select(d, "three", expected_version=1, command_id="revise")
    with pytest.raises(FrozenInstanceError):
        v1.selected = "three"
    assert v2.prior == v1.ref and d.versions("d") == (v1, v2)
    payload = history.events[0].payload
    payload["selected"] = "none"
    assert history.events[0].payload["selected"] == "one"
    assert CausalLink(v1.event_id, "direct_cause") in history.events[2].parents


def test_decision_using_delivered_distortion_retains_full_acquisition_and_access_ancestry():
    d, _, store, history, _ = world()
    claim(store, "original", "one", ("source",), actor="owner")
    clock = SimulationClock()
    net = Communication(store, clock, history, NamedRandomness(7))
    net.connect(Channel("edge", "owner", "a", 1, 1, distortion_probability=1,
                        distortion=DistortionRule("retry_count", "one", "three")),
                command_id="connect", correlation_id="case")
    net.send("edge", "original", command_id="send", correlation_id="case")
    events = net.deliver(clock.pop_next())
    transfer = events[-1]
    holding = store.view_for("a").entries[0].holding.holding_id
    store.set_holding_access(holding, False, tick=1, command_id="hide", correlation_id="case")
    access = store.set_holding_access(holding, True, tick=1, command_id="restore", correlation_id="case")[0]
    v = d.infer("d", "a", CapabilityProfile(("one", "three", "none")), expected_version=0,
                tick=1, command_id="infer", correlation_id="case")
    event = next(e for e in history.events if e.event_id == v.event_id)
    assert v.selected == "three" and "source" in v.source_ids
    assert CausalLink(transfer.event_id, "supporting_evidence") in event.parents
    assert CausalLink(access.event_id, "supporting_evidence") in event.parents
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_question_reference_cannot_launder_a_copy_of_an_existing_choice():
    d, _, store, history, q = world()
    v1 = select(d)
    claim(store, "copy", "one", v1.source_ids)
    v2 = select(d, expected_version=1, command_id="question-copy", evidence=(
        evidence("copy", q.ref, method="report"),))
    assert v2.support == "weak"
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_revising_justification_cannot_erase_the_original_source_dependency():
    d, _, store, history, _ = world()
    claim(store, "spec", "one", ("original-spec",))
    v1 = select(d, rationale_holding_ids=("spec",))
    v2 = select(d, expected_version=1, command_id="same-choice")
    claim(store, "copy", "one", ("original-spec",))
    v3 = select(d, expected_version=2, command_id="copy-of-original", evidence=(
        evidence("copy", v2.ref, method="report"),))
    assert set(v1.source_ids) <= set(v2.source_ids)
    assert v3.support == "weak"
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_delegated_grant_expiry_is_half_open_and_invalid_attempt_is_atomic():
    d, auth, _, history, _ = world()
    grant(auth, valid_until=2)
    auth.delegate("child", "root", "owner", "a", options=("one",), tick=0,
                  command_id="delegate", correlation_id="case")
    v1 = select(d, grant_id="child", tick=1)
    before = history.canonical_bytes()
    with pytest.raises(ValueError, match="expired"):
        select(d, grant_id="child", expected_version=1, tick=2)
    assert d.versions("d") == (v1,) and history.canonical_bytes() == before


def test_invalid_event_envelope_does_not_publish_a_grant_or_revoke_one():
    _, auth, _, history, _ = world()
    root = AuthorityGrant("root", "owner", "WI", ("one",), can_delegate=True)
    with pytest.raises(ValueError):
        auth.add_root(root, tick=0, command_id="", correlation_id="case")
    assert history.events == ()
    auth.add_root(root, tick=0, command_id="root", correlation_id="case")
    before = history.canonical_bytes()
    with pytest.raises(ValueError):
        auth.revoke("root", tick=0, command_id="", correlation_id="case")
    assert history.canonical_bytes() == before
    auth.delegate("child", "root", "owner", "a", options=("one",), tick=0,
                  command_id="delegate", correlation_id="case")


def test_capability_reads_accessible_claims_but_cannot_promote_them_to_evidence():
    d, _, store, history, _ = world()
    claim(store, "claim", "one", ("note",))
    v = d.infer("d", "a", CapabilityProfile(("three", "one", "none")), expected_version=0,
                tick=0, command_id="infer", correlation_id="case")
    assert v.selected == "one" and v.support == "none"
    assert decision_metrics(history).evidence_backed_information_gain == 0


def test_reusing_the_same_question_evidence_preserves_support_without_new_gain():
    d, _, store, history, question = world()
    claim(store, 'field-observation', 'one', ('observed-window',))
    assessment = evidence('field-observation', question.ref)
    first = select(d, evidence=(assessment,))
    assert first.support == 'supported'
    assert decision_metrics(history).evidence_backed_information_gain == 1
    second = select(d, expected_version=1, command_id='retain-evidence', evidence=(assessment,))
    assert second.support == 'supported'
    assert second.evidence[0].eligible
    assert decision_metrics(history).evidence_backed_information_gain == 1


@pytest.mark.parametrize("freshness, expected_support", [("current", "supported"), ("stale", "weak")])
def test_copy_of_already_admitted_evidence_preserves_support_without_extra_gain(freshness, expected_support):
    from agent_empires.simulation.knowledge import KnowledgeHolding, HolderRef
    d, _, store, history, question = world()
    item = claim(store, 'observation', 'one', ('observed-window',))
    first = select(d, evidence=(evidence('observation', question.ref),))
    assert first.support == 'supported'
    store.record_holding(KnowledgeHolding('documented-copy', item.ref, HolderRef('actor', 'a'),
                                          ('observed-window',), 'high', freshness, True),
                         tick=0, command_id='copy-evidence', correlation_id='case')
    store.set_holding_access('observation', False, tick=0, command_id='revoke-original',
                             correlation_id='case')
    second = select(d, expected_version=1, command_id='use-copy',
                    evidence=(evidence('documented-copy', question.ref),))
    assert second.support == expected_support
    assert decision_metrics(history).evidence_backed_information_gain == 1
