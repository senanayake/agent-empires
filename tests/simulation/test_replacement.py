"""Replacement must affect the live owners and actual queued delivery work."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.actors import Actor
from agent_empires.simulation.communication import Channel
from agent_empires.simulation.events import CausalLink, EntityRef
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem


INPUT = Path(__file__).resolve().parents[2] / 'scenarios/paymentco/scenario.json'


def service(seed=0, *, graph=True):
    engine = DeliveryService(load_scenario(INPUT), run_id='replacement-test', root_seed=seed)
    if graph:
        engine.communication  # explicitly initialize the authored graph for these graph tests
    return engine


def test_real_departure_cancels_unfinished_work_and_retains_cost():
    engine = service()
    job = engine.start('sarah', command_id='work')
    engine.knowledge.depart_actor('sarah', tick=0, command_id='depart', correlation_id='work')
    assert engine.step() is None
    assert engine.proposals == ()
    assert engine.spent_resource_units == job.resource_cost == 5
    cancelled = [e for e in engine.history.events if e.event_type == 'WorkCancelled']
    assert len(cancelled) == 1
    assert cancelled[0].payload['reason'] == 'actor_departed'
    assert {p.event_id for p in cancelled[0].parents} >= {job.event_id}
    assert engine.step() is None

NEW = Actor('replacement', 'agent', 'engineering')
FUNCTIONS = ('domain_interpreter', 'historian', 'product_engineering_bridge')


def replacement(engine, old='sarah', new=NEW, profile='implementer', command='replace'):
    return engine.replace_actor(old, new, profile_id=profile, role='senior engineer', command_id=command)


def register(engine, actor=NEW, profile='human'):
    engine.register_actor(actor, profile_id=profile, role='engineer', command_id='prepare')


def holding(engine, actor, topic=None):
    return next(e.holding.holding_id for e in engine.knowledge.view_for(actor).entries
                if topic is None or e.item.topic == topic)


def state(engine):
    return (engine.history.canonical_bytes(), engine.clock.now, engine.clock.pending_count,
            engine.spent_resource_units, engine.communication.total_cost,
            engine.communication.channels, engine.organization.uncovered_functions,
            tuple((a, engine.organization.role_for(a.actor_id), engine.knowledge.view_for(a.actor_id))
                  for a in engine.knowledge.actors))


def test_same_title_copies_no_knowledge_functions_channels_or_authority():
    engine = service()
    assert all(engine.organization.function_holders(f) == ('sarah',) for f in FUNCTIONS)
    prefix = engine.history.events
    replacement(engine)
    assert engine.history.events[:len(prefix)] == prefix
    assert engine.organization.role_for('sarah') is None
    assert engine.organization.role_for(NEW.actor_id) == 'senior engineer'
    assert 'sarah' not in engine.organization.members('engineering')
    assert NEW.actor_id in engine.organization.members('engineering')
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()
    assert set(FUNCTIONS) <= set(engine.organization.uncovered_functions)
    assert not engine.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1))
    assert not any(c.sender == 'sarah' or c.recipient == 'sarah' or NEW.actor_id in (c.sender, c.recipient)
                   for c in engine.communication.channels)
    with pytest.raises(ValueError):
        engine.authority.evaluate('grant.idempotency', NEW.actor_id, 'idempotency', 'stable_key', tick=0)
    assert not any(e.event_type == 'IncidentOccurred' for e in engine.history.events)


def test_redundant_holding_and_function_survive():
    engine = service()
    engine.organization.assign_function('historian', 'jin', tick=0,
        command_id='redundant.function', correlation_id='replace')
    engine.communication.send('sarah.to.jin', holding(engine, 'sarah'),
        command_id='redundant.holding', correlation_id='replace')
    engine.step()
    replacement(engine)
    assert engine.organization.function_holders('historian') == ('jin',)
    assert engine.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1))
    assert not any(e.event_type == 'KnowledgeLost' and e.payload['item_id'] == 'historical_scope'
                   for e in engine.history.events)
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()


def test_removed_bridge_does_not_implicitly_retarget_trust():
    engine = service()
    old = next(c for c in engine.communication.channels if c.channel_id == 'maya.to.sarah')
    replacement(engine)
    before = state(engine)
    with pytest.raises(ValueError):
        engine.communication.send(old.channel_id, holding(engine, 'maya'),
                                  command_id='stale.edge', correlation_id='replace')
    assert state(engine) == before
    fresh = Channel('maya.to.replacement', 'maya', NEW.actor_id, 1, 1, trust=0.1)
    engine.communication.connect(fresh, command_id='connect.new', correlation_id='replace')
    assert next(c for c in engine.communication.channels if c.channel_id == fresh.channel_id).trust == 0.1
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()


def test_explicit_delegation_adds_authority_without_knowledge_and_revokes_departed_grants():
    engine = service()
    engine.authority.delegate('sarah.discretion', 'grant.idempotency', 'ada', 'sarah',
        options=('stable_key',), tick=0, command_id='delegate.old', correlation_id='replace')
    old = engine.decisions.select('idempotency', 'stable_key', actor_id='sarah', grant_id='sarah.discretion',
        expected_version=0, tick=0, command_id='select.old', correlation_id='replace', reason='delegated')
    replacement(engine)
    with pytest.raises(ValueError):
        engine.authority.evaluate('sarah.discretion', 'sarah', 'idempotency', 'stable_key', tick=0)
    assert any(e.event_type == 'AuthorityRevoked' and e.payload['grant_id'] == 'sarah.discretion'
               for e in engine.history.events)
    engine.authority.delegate('new.discretion', 'grant.idempotency', 'ada', NEW.actor_id,
        options=('stable_key',), tick=0, command_id='delegate.new', correlation_id='replace')
    new = engine.decisions.select('idempotency', 'stable_key', actor_id=NEW.actor_id, grant_id='new.discretion',
        expected_version=1, tick=0, command_id='select.new', correlation_id='replace', reason='delegated')
    assert new.authority_basis == 'delegated_discretion' and new.support == 'none'
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()
    assert engine.decisions.version('idempotency', 1) == old


def test_departed_grantor_invalidates_descendants_without_rewriting_old_choice():
    engine = service()
    register(engine)
    engine.authority.delegate('prepared', 'grant.idempotency', 'ada', NEW.actor_id,
        options=('stable_key',), tick=0, command_id='delegate', correlation_id='replace')
    old = engine.decisions.select('idempotency', 'stable_key', actor_id=NEW.actor_id, grant_id='prepared',
        expected_version=0, tick=0, command_id='choose', correlation_id='replace', reason='delegated')
    replacement(engine, old='ada', new=Actor('architect', 'agent', 'architecture'))
    with pytest.raises(ValueError):
        engine.authority.evaluate('prepared', NEW.actor_id, 'idempotency', 'stable_key', tick=0)
    assert engine.decisions.version('idempotency', 1) == old


def test_inflight_sender_snapshot_survives_retirement_and_recipient_departure_loses_message():
    engine = service()
    engine.communication.send('sarah.to.jin', holding(engine, 'sarah'), command_id='outgoing', correlation_id='replace')
    engine.communication.send('maya.to.sarah', holding(engine, 'maya'), command_id='incoming', correlation_id='replace')
    cost = engine.communication.total_cost
    replacement(engine)
    assert engine.clock.pending_count == 2
    engine.step()
    assert engine.knowledge.view_for('jin').lookup('historical_scope', 1)
    losses = [e for e in engine.history.events if e.event_type == 'InformationLost']
    assert len(losses) == 1 and losses[0].payload['reason'] == 'recipient_unavailable'
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()
    assert engine.communication.total_cost == cost
    assert engine.clock.pending_count == 0


def test_replacement_immediately_cancels_old_work_and_new_actor_executes_real_work():
    engine = service()
    old_job = engine.start('sarah', command_id='old.work')
    replacement(engine)
    cancelled = next(e for e in engine.history.events if e.event_type == 'WorkCancelled')
    assert cancelled.tick == 0
    assert CausalLink(old_job.event_id, 'direct_cause') in cancelled.parents
    new_job = engine.start(NEW.actor_id, command_id='new.work')
    assert new_job.resource_cost == 2 and new_job.completion_tick == 1
    result = engine.step()
    assert result.proposal.actor_id == NEW.actor_id
    assert engine.step() is None
    assert len(engine.proposals) == 1
    assert engine.spent_resource_units == old_job.resource_cost + new_job.resource_cost
    assert len([e for e in engine.history.events if e.event_type == 'WorkCancelled']) == 1


def test_new_actor_inference_uses_live_claims_not_initial_scenario_roster():
    engine = service()
    replacement(engine)
    claim = KnowledgeItem('runtime.count', 1, 'retry_count', 'one')
    engine.knowledge.register_item(claim)
    engine.knowledge.record_holding(KnowledgeHolding('received', claim.ref,
        HolderRef('actor', NEW.actor_id), ('explicit.runtime.claim',), 'high', 'current', True),
        tick=0, command_id='receive', correlation_id='replace')
    engine.start(NEW.actor_id, command_id='new')
    chosen = engine.decisions.version('retry_count', 1)
    assert chosen.selected == 'one' and chosen.rationale
    assert chosen.support == 'none'
    assert engine.step().proposal.actor_id == NEW.actor_id


def test_completed_artifacts_survive_replacement_unchanged():
    engine = service()
    engine.start('sarah', command_id='done')
    proposal = engine.step().proposal
    replacement(engine)
    assert engine.proposals == (proposal,)
    assert not any(e.event_type == 'WorkCancelled' for e in engine.history.events)


def test_noncritical_replacement_preserves_other_functions_knowledge_and_graph():
    engine = service()
    entry = engine.knowledge.view_for('sarah')
    edges = tuple(c for c in engine.communication.channels if 'jin' not in (c.sender, c.recipient))
    replacement(engine, old='jin')
    assert engine.knowledge.view_for('sarah') == entry
    assert engine.organization.uncovered_functions == ()
    assert engine.communication.channels == edges
    assert all(engine.organization.function_holders(f) == ('sarah',) for f in FUNCTIONS)


def test_fully_prepared_matched_profile_preserves_coverage_access_authority_and_behavior():
    baseline, prepared = service(), service()
    register(prepared)
    prepared.communication.connect(Channel('handover', 'sarah', NEW.actor_id, 1, 1),
        command_id='connect', correlation_id='prepare')
    prepared.communication.send('handover', holding(prepared, 'sarah'), command_id='transfer', correlation_id='prepare')
    prepared.step()
    for f in FUNCTIONS:
        prepared.organization.assign_function(f, NEW.actor_id, tick=1, command_id='assign.' + f, correlation_id='prepare')
    prepared.authority.delegate('new.idempotency', 'grant.idempotency', 'ada', NEW.actor_id,
        options=('stable_key',), tick=1, command_id='delegate', correlation_id='prepare')
    old_edges = tuple(c for c in prepared.communication.channels
                      if 'sarah' in (c.sender, c.recipient) and c.channel_id != 'handover')
    replacement(prepared, profile='human')
    for edge in old_edges:
        prepared.communication.connect(replace(edge, channel_id='new.' + edge.channel_id,
            sender=NEW.actor_id if edge.sender == 'sarah' else edge.sender,
            recipient=NEW.actor_id if edge.recipient == 'sarah' else edge.recipient),
            command_id='reconnect.' + edge.channel_id, correlation_id='prepare')
    mapped_edges = {(c.sender.replace(NEW.actor_id, 'sarah'), c.recipient.replace(NEW.actor_id, 'sarah'), c.trust)
                    for c in prepared.communication.channels if c.channel_id != 'handover'}
    assert mapped_edges == {(c.sender, c.recipient, c.trust) for c in baseline.communication.channels}
    assert prepared.organization.uncovered_functions == ()
    assert prepared.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1))
    assert all(prepared.organization.function_holders(f) == (NEW.actor_id,) for f in FUNCTIONS)
    prepared.authority.evaluate('new.idempotency', NEW.actor_id, 'idempotency', 'stable_key', tick=1)
    old_job = baseline.start('sarah', command_id='old')
    new_job = prepared.start(NEW.actor_id, command_id='new')
    assert (new_job.completion_tick-new_job.started_tick, new_job.resource_cost) == (
        old_job.completion_tick-old_job.started_tick, old_job.resource_cost)
    assert prepared.step().proposal.behavior == baseline.step().proposal.behavior


@pytest.mark.parametrize('old,new,profile,role', [
    ('missing', NEW, 'implementer', 'engineer'),
    ('sarah', Actor('sarah', 'agent', 'engineering'), 'implementer', 'engineer'),
    ('sarah', Actor('jin', 'agent', 'engineering'), 'implementer', 'engineer'),
    ('sarah', NEW, 'missing', 'engineer'),
    ('sarah', NEW, 'implementer', ''),
    ('sarah', NEW, 'implementer', None),
])
def test_rejected_replacement_does_not_mutate_any_owner(old, new, profile, role):
    engine = service()
    engine.start('sarah', command_id='pending')
    before = state(engine)
    with pytest.raises((ValueError, TypeError)):
        engine.replace_actor(old, new, profile_id=profile, role=role, command_id='invalid')
    assert state(engine) == before
    assert engine.step().proposal.actor_id == 'sarah'


def test_duplicate_replacement_and_departed_id_reuse_are_rejected_without_mutation():
    engine = service()
    replacement(engine)
    before = state(engine)
    with pytest.raises(ValueError):
        replacement(engine, command='again')
    with pytest.raises(ValueError):
        engine.register_actor(Actor('sarah', 'agent', 'engineering'), profile_id='human',
                              role='engineer', command_id='reuse')
    assert state(engine) == before


def test_invalid_function_assignment_and_actor_registration_do_not_mutate():
    engine = service()
    before = state(engine)
    with pytest.raises(ValueError):
        engine.organization.assign_function('missing', 'jin', tick=0, command_id='invalid', correlation_id='replace')
    with pytest.raises(ValueError):
        engine.register_actor(NEW, profile_id='missing', role='engineer', command_id='invalid')
    assert state(engine) == before


def test_replacement_at_due_tick_cancels_before_completion_if_command_arrives_first():
    engine = service()
    job = engine.start('sarah', command_id='work')
    engine.clock.advance_to(job.completion_tick)
    replacement(engine)
    assert engine.step() is None and engine.proposals == ()


def test_replacement_rejects_history_ahead_of_clock_without_advancing_or_skipping_work():
    engine = service()
    engine.start('sarah', command_id='work')
    engine.history.append(tick=2, event_type='ExternalFact', command_id='future', correlation_id='future', payload={})
    before = state(engine)
    with pytest.raises(ValueError):
        replacement(engine)
    assert state(engine) == before


def test_matched_actor_kind_and_renamed_critical_actor_move_same_vulnerability(tmp_path):
    histories = []
    for kind in ('agent', 'human'):
        engine = service()
        replacement(engine, new=replace(NEW, kind=kind))
        histories.append([e.as_dict() for e in engine.history.events if e.event_type != 'ActorRegistered'])
    assert histories[0] == histories[1]
    data = json.loads(INPUT.read_text())
    for actor in data['actors']:
        if actor['actor_id'] == 'sarah':
            actor['actor_id'] = 'renamed'
    for h in data['holdings']:
        if h['holder']['holder_id'] == 'sarah':
            h['holder']['holder_id'] = 'renamed'
    for f in data['functions']:
        f['actor_ids'] = ['renamed' if a == 'sarah' else a for a in f['actor_ids']]
    for c in data['channels']:
        for key in ('sender', 'recipient'):
            if c[key] == 'sarah':
                c[key] = 'renamed'
    path = tmp_path / 'renamed.json'
    path.write_text(json.dumps(data))
    renamed = DeliveryService(load_scenario(path), run_id='replacement-test')
    replacement(renamed, old='renamed')
    assert set(FUNCTIONS) <= set(renamed.organization.uncovered_functions)
    assert not renamed.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1))


@pytest.mark.parametrize('seed', range(16))
def test_seeded_admitted_snapshot_is_paired_and_not_resampled_after_replacement(seed):
    engines = [service(seed), service(seed)]
    for engine in engines:
        engine.communication.connect(Channel('paired', 'sarah', 'jin', 2, 1, loss_probability=0.4),
            command_id='paired.connect', correlation_id='paired')
        engine.communication.send('paired', holding(engine, 'sarah'), command_id='paired.send', correlation_id='paired')
    replacement(engines[1])
    for engine in engines:
        engine.step()
    outcomes = [next(e for e in engine.history.events
                     if e.command_id == 'paired.send' and e.event_type in ('InformationLost', 'KnowledgeTransferred'))
                for engine in engines]
    assert outcomes[0].event_type == outcomes[1].event_type
    assert outcomes[0].payload == outcomes[1].payload
    assert engines[0].knowledge.view_for('jin') == engines[1].knowledge.view_for('jin')


def test_replacement_replay_and_multiple_pending_jobs_resolve_once_in_queue_order():
    histories = []
    for _ in range(2):
        engine = service()
        for command in ('first', 'second'):
            engine.start('sarah', command_id=command)
        replacement(engine)
        engine.start(NEW.actor_id, command_id='new')
        engine.step()
        assert engine.step() is None
        cancelled = [e.correlation_id for e in engine.history.events if e.event_type == 'WorkCancelled']
        assert cancelled == ['first', 'second']
        assert len(engine.proposals) == 1 and engine.clock.pending_count == 0
        histories.append(engine.history.canonical_bytes())
    assert histories[0] == histories[1]


def test_reserved_work_namespace_and_prepared_profile_change_reject_without_mutation():
    engine = service()
    register(engine)
    before = state(engine)
    with pytest.raises(ValueError):
        engine.start('sarah', command_id='communication:collision')
    with pytest.raises(ValueError):
        replacement(engine, profile='implementer')
    assert state(engine) == before


def test_new_registration_supplies_no_artifact_reader_and_rejects_invalid_fact_metadata():
    engine = service()
    before = state(engine)
    with pytest.raises(ValueError):
        engine.knowledge.register_actor(NEW, tick=0, command_id='new', correlation_id=' ',
                                       parents=(CausalLink('missing', 'direct_cause'),))
    assert state(engine) == before
    register(engine)
    assert engine.knowledge.view_for(NEW.actor_id).entries == ()
    assert NEW.actor_id in engine.organization.members('engineering')


def test_replacement_command_retry_cannot_replace_another_actor():
    engine = service()
    replacement(engine)
    before = state(engine)
    with pytest.raises(ValueError):
        replacement(engine, old='jin', new=Actor('next', 'agent', 'engineering'))
    assert state(engine) == before


def test_delivery_without_communication_preserves_existing_history_boundary():
    engine = service(graph=False)
    engine.start('sarah', command_id='work')
    engine.step()
    assert not any(e.event_type == 'ChannelConnected' for e in engine.history.events)


def test_rejected_cold_replacement_does_not_initialize_graph_or_register_actor():
    engine = service(graph=False)
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError):
        replacement(engine, profile='missing')
    assert engine.history.canonical_bytes() == before
