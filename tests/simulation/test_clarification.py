import pytest

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.communication import Channel
from agent_empires.simulation.decisions import AuthorityGrant, AuthorityRegistry, CapabilityProfile, DecisionQuestion, Decisions
from agent_empires.simulation.events import EventHistory
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore
from agent_empires.simulation.learning import Clarification
from agent_empires.simulation.randomness import NamedRandomness


def setup(*, claims=('safe',), freshness='current', latency=2, loss=0, scope='payments', expiry=None, kind='human'):
    history, clock = EventHistory('clarify'), SimulationClock()
    store = KnowledgeStore(history, [Actor('worker', 'agent', 'dev'), Actor('holder', kind, 'ops')])
    for i, claim in enumerate(claims):
        item = KnowledgeItem(f'item{i}', 1, 'key', claim)
        store.register_item(item)
        store.record_holding(KnowledgeHolding(f'h{i}', item.ref, HolderRef('actor', 'holder'),
                                              ('interface',), 'high', freshness),
                             tick=0, command_id=f'holding{i}', correlation_id='setup')
    authority = AuthorityRegistry(store, history)
    authority.add_root(AuthorityGrant('grant', 'holder', scope, ('safe', 'unsafe'), valid_until=expiry),
                       tick=0, command_id='grant', correlation_id='setup')
    question = DecisionQuestion('key', 'key', 'payments', ('safe', 'unsafe'))
    owner = Clarification(store, authority, clock, history, NamedRandomness(7))
    owner.connect(Channel('ask', 'worker', 'holder', latency, 1, transfer_cost=2))
    owner.connect(Channel('answer', 'holder', 'worker', latency, 1, loss_probability=loss, transfer_cost=3))
    return owner, store, authority, clock, history, question


def ask(env, **kwargs):
    owner, _, _, _, _, question = env
    return owner.ask(question, requester='worker', holder='holder', request_channel='ask',
                     answer_channel='answer', command_id='query', timeout=10, grant_id='grant', **kwargs)


def drain(env):
    owner, _, _, clock, _, _ = env
    while (work := clock.pop_next()) is not None:
        owner.dispatch(work)
    return owner.result('query')


def test_useful_answer_changes_option_after_round_trip_without_granting_requester_authority():
    env = setup()
    owner, store, authority, clock, history, question = env
    decisions = Decisions(store, authority, history)
    decisions.register(question)
    profile = CapabilityProfile(('unsafe', 'safe'))
    old = decisions.infer('key', 'worker', profile, expected_version=0, tick=0,
                          command_id='infer', correlation_id='story')
    ask(env, available_at=5, service_ticks=1)
    assert not store.view_for('worker').entries
    result = drain(env)
    assert result.completed_tick == 8
    assert result.elapsed_ticks == 8 and owner.total_cost == 5
    assert result.source_ids == ('interface',)
    assert result.answers[0].authority_status == 'valid'
    revised = owner.select('query', decisions, profile, expected_version=1, command_id='revise')
    assert old.selected == 'unsafe' and revised.selected == 'safe'
    assert revised.authority_basis == 'inferred_without_authority'
    assert revised.support == 'none' and revised.backed_source_ids == ()
    assert result.event_id in [p.event_id for p in history.events[-2].parents]


@pytest.mark.parametrize('holder,answer', [('missing', 'answer'), ('holder', 'ask')])
def test_missing_holder_or_reverse_path_rejected_without_mutation(holder, answer):
    env = setup()
    owner, _, _, clock, history, question = env
    before = history.canonical_bytes(), clock.pending_count, owner.total_cost
    with pytest.raises(ValueError):
        owner.ask(question, requester='worker', holder=holder, request_channel='ask',
                  answer_channel=answer, command_id='query', timeout=10)
    assert before == (history.canonical_bytes(), clock.pending_count, owner.total_cost)


@pytest.mark.parametrize('scope,expiry', [('other', None), ('payments', 4)])
def test_authority_scope_and_expiry_do_not_erase_answer_sources(scope, expiry):
    env = setup(scope=scope, expiry=expiry)
    ask(env)
    result = drain(env)
    assert result.source_ids == ('interface',)
    assert result.answers[0].authority_status == 'invalid'
    assert result.answers[0].grant_ref is None


def test_stale_answer_recorded_but_not_used_for_choice():
    env = setup(freshness='stale')
    ask(env)
    result = drain(env)
    assert result.answers[0].freshness == 'stale'
    assert env[0].propose('query', CapabilityProfile(('unsafe', 'safe')))[0] == 'unsafe'


@pytest.mark.parametrize('available,service', [(None, 0), (9, 0), (0, 9)])
def test_timeout_consumes_wait_and_does_not_acquire_late_answer(available, service):
    env = setup()
    ask(env, available_at=available, service_ticks=service)
    result = drain(env)
    assert result.status == 'timed_out' and result.elapsed_ticks == 10
    assert not env[1].view_for('worker').entries


def test_answer_exactly_at_deadline_succeeds():
    env = setup()
    ask(env, available_at=8)
    assert drain(env).status == 'answered'


def test_conflicting_and_duplicate_source_answers_do_not_vote_or_hide_conflict():
    env = setup(claims=('safe', 'unsafe', 'safe'))
    ask(env)
    result = drain(env)
    assert result.status == 'conflicted' and result.source_ids == ('interface',)
    assert len(result.answers) == 3 and result.completed_tick == 6
    assert env[0].total_cost == 11
    assert env[0].propose('query', CapabilityProfile(('unsafe', 'safe')))[0] == 'unsafe'


def test_wrong_answer_is_usable_without_truth_oracle():
    env = setup(claims=('unsafe',))
    ask(env)
    assert drain(env).status == 'answered'
    assert env[0].propose('query', CapabilityProfile(('safe', 'unsafe')))[0] == 'unsafe'


def test_loss_and_departure_preserve_negative_outcomes():
    env = setup(loss=1)
    ask(env)
    result = drain(env)
    assert result.status == 'no_answer' and not result.answers and env[0].total_cost == 5
    env = setup()
    ask(env)
    env[1].depart_actor('holder', tick=0, command_id='depart', correlation_id='setup')
    assert drain(env).status == 'timed_out'


def test_access_checked_at_response_not_request_and_catalog_never_answers():
    env = setup()
    ask(env)
    env[1].set_holding_access('h0', False, tick=0, command_id='hide', correlation_id='setup')
    secret = KnowledgeItem('secret', 1, 'key', 'safe')
    env[1].register_item(secret)
    assert drain(env).status == 'no_answer'
    assert not env[1].view_for('worker').entries


def test_capacity_duplicate_commands_and_bad_time_fail_atomically():
    env = setup()
    ask(env)
    owner, _, _, clock, history, question = env
    before = history.canonical_bytes(), clock.pending_count, owner.total_cost
    for command, timeout in [('query', 10), ('second', 10), ('bad', True)]:
        with pytest.raises((ValueError, TypeError)):
            owner.ask(question, requester='worker', holder='holder', request_channel='ask',
                      answer_channel='answer', command_id=command, timeout=timeout)
        assert before == (history.canonical_bytes(), clock.pending_count, owner.total_cost)


def test_matched_actor_kind_and_seed_repeat_preserve_canonical_history():
    histories = []
    for kind in ('human', 'agent', 'human'):
        env = setup(kind=kind)
        ask(env)
        drain(env)
        histories.append(env[4].canonical_bytes())
    assert histories[0] == histories[1] == histories[2]


def test_restored_access_retains_acquisition_and_latest_permission_lineage():
    env = setup()
    env[1].set_holding_access('h0', False, tick=0, command_id='hide', correlation_id='setup')
    restored = env[1].set_holding_access('h0', True, tick=0, command_id='restore', correlation_id='setup')[0]
    ask(env)
    drain(env)
    sent = next(e for e in env[4].events if e.event_type == 'ClarificationAnswerSent')
    assert restored.event_id in [p.event_id for p in sent.parents]
    assert any(p.event_id == env[4].events[0].event_id for p in sent.parents)


def test_truncated_batch_keeps_deadline_answer_and_partial_status():
    env = setup(claims=('safe', 'unsafe', 'safe', 'unsafe', 'safe', 'unsafe', 'safe', 'unsafe'))
    ask(env)
    result = drain(env)
    assert result.status == 'timed_out' and result.completed_tick == 10
    assert len(result.answers) == 7  # boundary arrival retained before timeout
    assert len(env[1].view_for('worker').entries) == 7


def test_paired_experiment_helpful_and_harmless_costs_and_seed_repeat():
    from experiments.clarification_comparison import load_inputs, paired_case
    data, protocol = load_inputs()
    pairs = [paired_case(data, protocol, 'world_a', 0, 'helpful', protocol['timing_profiles'][0])
             for _ in range(2)]
    assert pairs[0] == pairs[1]
    pair = pairs[0]
    assert pair['inference']['workload_sha256'] == pair['clarification']['workload_sha256']
    assert pair['inference']['selected'] == 'new_key'
    assert pair['clarification']['selected'] == 'stable_key'
    assert pair['clarification']['metrics']['duplicate_charges'] == 0
    benign = paired_case(data, protocol, 'world_a', 0, 'harmless', protocol['timing_profiles'][0])
    assert benign['inference']['metrics']['duplicate_charges'] == 0
    assert benign['clarification']['metrics']['duplicate_charges'] == 0
    assert benign['differences']['ship_ticks'] > 0
    assert benign['cost_grid']['duplicate=20/delay=4'] > 0


def test_experiment_author_verify_overwrite_tamper_and_fresh_budget(tmp_path):
    import json
    from experiments.clarification_comparison import author, load_inputs, verify
    _, protocol = load_inputs()
    # Small held-fixed protocol for CLI contract checks; production uses all seeds.
    protocol = {**protocol, 'seeds': [0], 'worlds': ['world_a'], 'conditions': ['helpful', 'harmless'],
                'timing_profiles': protocol['timing_profiles'][:1]}
    directory = tmp_path / 'evidence'
    author(directory, protocol)
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    verify(directory, protocol)
    assert before == {p.name: p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(FileExistsError):
        author(directory, protocol)
    results = directory / 'results.json'
    saved = json.loads(results.read_text())
    saved['pairs'] = {}
    results.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match='canonical'):
        verify(directory, protocol)
    with pytest.raises(RuntimeError, match='budget'):
        author(tmp_path / 'too-slow', {**protocol, 'wall_budget_seconds': 0})


def test_rejected_authority_claim_id_survives_in_answer_audit():
    env = setup(scope='other')
    ask(env)
    drain(env)
    requested = next(e for e in env[4].events if e.event_type == 'ClarificationRequested')
    answer = next(e for e in env[4].events if e.event_type == 'KnowledgeTransferred')
    assert requested.payload['claimed_grant_id'] == 'grant'
    assert answer.payload['claimed_grant_id'] == 'grant'
    assert answer.payload['authority_status'] == 'invalid'


def test_distortion_and_request_loss_have_audit_and_preserve_sources():
    from agent_empires.simulation.communication import DistortionRule
    env = setup()
    env[0].connect(Channel('distorted', 'holder', 'worker', 2, 1, distortion_probability=1,
                          distortion=DistortionRule('key', 'safe', 'unsafe')))
    env[0].ask(env[5], requester='worker', holder='holder', request_channel='ask', answer_channel='distorted',
               command_id='query', timeout=10)
    result = drain(env)
    assert result.answers[0].proposition == 'unsafe' and result.source_ids == ('interface',)
    event = next(e for e in env[4].events if e.event_type == 'KnowledgeTransferred')
    assert event.payload['distorted'] and event.payload['original_item'] != event.payload['received_item']
    env = setup()
    env[0].connect(Channel('request-loss', 'worker', 'holder', 1, 1, loss_probability=1, transfer_cost=2))
    env[0].ask(env[5], requester='worker', holder='holder', request_channel='request-loss', answer_channel='answer',
               command_id='query', timeout=10)
    assert drain(env).status == 'timed_out' and env[0].total_cost == 2


def test_foreign_or_duplicate_dispatch_does_not_consume_work():
    env = setup()
    ask(env)
    foreign = env[3].schedule(1, 'other-owner')
    assert env[3].pop_next() == foreign
    before = env[4].canonical_bytes()
    with pytest.raises(ValueError):
        env[0].dispatch(foreign)
    assert env[4].canonical_bytes() == before
    work = env[3].pop_next()
    env[0].dispatch(work)
    with pytest.raises(ValueError):
        env[0].dispatch(work)
    assert drain(env).status == 'answered'
