"""Exposure, paired controls and delayed feedback for the PaymentCo world."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.outcomes import (
    PaymentInput, PaymentOutcomes, WorldRules, generate_workload,
)

ROOT = Path(__file__).resolve().parents[2]


def delivery(tmp_path, *, kind='agent', choices=None):
    data = json.loads((ROOT / 'scenarios/paymentco/scenario.json').read_bytes())
    next(a for a in data['actors'] if a['actor_id'] == 'jin').update(kind=kind, profile_id='implementer')
    path = tmp_path / 'scenario.json'
    path.write_text(json.dumps(data))
    service = DeliveryService(load_scenario(path), run_id='payment-test')
    for name, option in (choices or {}).items():
        service.decisions.select(name, option, actor_id='jin', expected_version=0, tick=0,
                                 command_id='choose.' + name, correlation_id='payment',
                                 reason='authored control choice', missing_information=('unvalidated:' + name,))
    service.start('jin', command_id='work')
    verification = service.step()
    assert all(c.passed for c in verification.checks)
    return service, verification.proposal


def world(**changes):
    return replace(WorldRules('test-world', (1, 0, 0, 0), (1, 0, 0, 1),
                              1, 1, 1, 5, 1, 1), **changes)


def payment(category='transient', *, arrival=0, hidden=0, recovery=(0, 0, 0),
            abandon=(0, 0, 0, 0), operation='p'):
    return PaymentInput(operation, arrival, category, hidden, recovery, abandon)


def launch(tmp_path, workload, *, rules=None, choices=None, kind='agent'):
    service, proposal = delivery(tmp_path, kind=kind, choices=choices or {'backoff': 'fixed'})
    engine = PaymentOutcomes(rules or world(), service.history, service.clock)
    deployment = engine.ship(proposal, workload, command_id='ship')
    return service, engine, deployment


def drain(engine):
    while engine.step() is not None:
        pass
    return engine.metrics()


def test_shipping_schedules_exposure_and_later_observation(tmp_path):
    service, engine, deployment = launch(tmp_path, (payment(arrival=3),))
    assert service.clock.pending_count == 1
    assert engine.results == engine.observations == ()
    engine.step()  # initial failure arrives at ship tick 1 + offset 3
    assert service.clock.now == 4 and engine.results == ()
    engine.step()  # recover at fixed delay 2
    assert service.clock.now == 6 and engine.results[0].completed
    assert engine.observations == () and service.clock.pending_count == 1
    engine.step()
    assert service.clock.now == 11
    observed = engine.observations[0]
    assert observed.payload['outcome_tick'] == 6
    assert observed.payload['deployment'] == deployment.ref.as_dict()
    assert engine.step() is None


def test_same_implementation_favorable_and_unfavorable_workload(tmp_path):
    _, favorable, _ = launch(tmp_path, (payment(),))
    good = drain(favorable)
    _, unfavorable, _ = launch(tmp_path, (payment('hard_decline'),))
    bad = drain(unfavorable)
    assert good['completed'] == good['recovered'] == 1
    assert good['abandoned'] == good['duplicate_charges'] == 0
    assert bad['abandoned'] == 1 and bad['completed'] == 0
    assert bad['retry_cost'] == 0  # decline prohibited by this implementation


def test_repeated_declines_stop_at_abandonment_and_charge_actual_attempts(tmp_path):
    choices = {'retryable_types': 'all_failures', 'declined_handling': 'retry_all', 'backoff': 'fixed'}
    sample = payment('hard_decline', abandon=(0.9, 0.9, 0.1, 0.1))
    _, engine, _ = launch(tmp_path, (sample,), rules=world(abandonment_probability=0.5), choices=choices)
    result = drain(engine)
    assert result['retry_attempts'] == result['retry_cost'] == 2
    assert result['abandoned'] == 1 and result['completed'] == 0
    assert result['total_attempts'] == 3  # unused third retry neither runs nor costs


def test_safe_unsafe_held_fixed_ambiguous_exposure(tmp_path):
    choices = {'retryable_types': 'all_failures', 'backoff': 'fixed'}
    workload = (payment('ambiguous'),)
    _, safe, _ = launch(tmp_path, workload, choices=choices)
    safe_metrics = drain(safe)
    service, unsafe, deployment = launch(tmp_path, workload, choices={**choices, 'idempotency': 'new_key'})
    unsafe_metrics = drain(unsafe)
    assert safe_metrics['completed'] == unsafe_metrics['completed'] == 1
    assert safe_metrics['duplicate_charges'] == 0 < unsafe_metrics['duplicate_charges'] == 1
    incident = next(e for e in service.history.events if e.event_type == 'IncidentOccurred')
    assert incident.payload['deployment'] == deployment.ref.as_dict()
    pinned = next(d for d in unsafe.deployments[0].proposal.decisions if d.decision_id == 'idempotency')
    assert incident.payload['decision'] == pinned.ref.as_dict()
    assert incident.payload['information_gaps']
    assert any(p.event_id == pinned.event_id for p in incident.parents)
    events = {e.event_id: e for e in service.history.events}
    assert all(events[g['event_id']].event_type == 'AssumptionMade'
               for g in incident.payload['information_gaps'])
    ancestry = set()
    def visit(event_id):
        if event_id in ancestry:
            return
        ancestry.add(event_id)
        for link in events[event_id].parents:
            visit(link.event_id)
    visit(incident.event_id)
    assert {'GoalDeclared', 'WorkItemCreated', 'DecisionSelected', 'WorkStarted',
            'ChangeProposalCreated', 'DeploymentCompleted', 'PaymentAttempted'} <= {
                events[e].event_type for e in ancestry}


@pytest.mark.parametrize('hidden,recovery', [(0.99, (0, 0, 0)), (0, (0.99, 0.99, 0.99))])
def test_unsupported_unsafe_choice_can_be_harmless(tmp_path, hidden, recovery):
    _, engine, _ = launch(tmp_path, (payment('ambiguous', hidden=hidden, recovery=recovery),),
                          rules=world(duplicate_probability=0.5, recovery=(1, 0, 0, 0.5)),
                          choices={'retryable_types': 'all_failures', 'backoff': 'fixed', 'idempotency': 'new_key'})
    assert engine.deployments[0].proposal.unsupported_decisions
    assert drain(engine)['duplicate_charges'] == 0


def test_no_traffic_has_no_incident_or_fabricated_goal_rate(tmp_path):
    service, engine, _ = launch(tmp_path, ())
    metrics = drain(engine)
    assert metrics['eligible'] == metrics['duplicate_charges'] == metrics['observed_count'] == 0
    assert metrics['abandonment_rate'] is None
    assert not any(e.event_type == 'IncidentOccurred' for e in service.history.events)


def test_harmful_human_successful_agent_and_matched_kind_history(tmp_path):
    workload = (payment('ambiguous'),)
    risky = {'retryable_types': 'all_failures', 'idempotency': 'new_key', 'backoff': 'fixed'}
    human_service, human, _ = launch(tmp_path, workload, choices=risky, kind='human')
    agent_service, matched, _ = launch(tmp_path, workload, choices=risky, kind='agent')
    assert drain(human)['duplicate_charges'] == drain(matched)['duplicate_charges'] == 1
    assert human_service.history.canonical_bytes() == agent_service.history.canonical_bytes()
    _, safe, _ = launch(tmp_path, workload, choices={**risky, 'idempotency': 'stable_key'}, kind='agent')
    assert drain(safe)['completed'] == 1 and safe.metrics()['duplicate_charges'] == 0


def test_lag_changes_observation_time_only(tmp_path):
    service, slow, _ = launch(tmp_path, (payment(),))
    _, fast, _ = launch(tmp_path, (payment(),), rules=world(observation_lag=0))
    assert drain(slow) == drain(fast)
    assert slow.results == fast.results
    assert slow.observations[0].tick - fast.observations[0].tick == 5
    assert service.history.events[-1].tick == slow.observations[0].tick


def test_immediate_retry_negative_and_readiness_boundary(tmp_path):
    _, immediate, _ = launch(tmp_path, (payment(),), choices={'backoff': 'immediate'})
    assert drain(immediate)['recovered'] == 0
    assert immediate.metrics()['retry_attempts'] == 3
    _, ready, _ = launch(tmp_path, (payment(),), rules=world(recovery_delay=2))
    assert drain(ready)['recovered'] == 1  # inclusive readiness boundary


def test_seeded_workload_repeats_and_is_held_fixed_across_strategies(tmp_path):
    rules = world(mix=(0.4, 0.2, 0.15, 0.25), recovery=(0.65, 0.02, 0, 0.4),
                  duplicate_probability=0.3, abandonment_probability=0.7, workload_rate=2)
    workload = generate_workload(rules, seed=17, arrival_window=10)
    assert workload == generate_workload(rules, seed=17, arrival_window=10)
    assert len(workload) == 20 and workload != generate_workload(rules, seed=18, arrival_window=10)
    _, engine, _ = launch(tmp_path, workload, rules=rules)
    _, repeat, _ = launch(tmp_path, workload, rules=rules)
    assert drain(engine) == drain(repeat) and engine.results == repeat.results
    assert generate_workload(replace(rules, recovery=(0, 0, 0, 0), observation_lag=0),
                             seed=17, arrival_window=10) == workload


def test_authorized_blanket_policy_can_miss_soft_recovery(tmp_path):
    service, proposal = delivery(tmp_path, choices={'backoff': 'fixed', 'retryable_types': 'all_failures'})
    # Explicit policy revision through the existing decision API, then a new proposal.
    service.decisions.select('declined_handling', 'do_not_retry', actor_id='priya', expected_version=1,
                             tick=1, command_id='policy', correlation_id='payment',
                             grant_id='grant.declined_handling', reason='authored initial policy')
    service.start('jin', command_id='policy-work')
    authorized = service.step().proposal
    engine = PaymentOutcomes(world(recovery=(1, 1, 0, 1)), service.history, service.clock)
    engine.ship(authorized, (payment('soft_decline'),), command_id='policy-ship')
    assert drain(engine)['abandoned'] == 1
    _, alternative, _ = launch(tmp_path, (payment('soft_decline'),), rules=world(recovery=(1, 1, 0, 1)),
                               choices={'backoff': 'fixed', 'retryable_types': 'all_failures', 'declined_handling': 'soft_only'})
    assert drain(alternative)['recovered'] == 1


def test_delayed_old_deployment_observation_keeps_pinned_decisions(tmp_path):
    service, engine, first = launch(tmp_path, (payment(),))
    engine.step()
    engine.step()  # old outcome occurred; observation pending
    prior = first.proposal.decisions[1]
    service.decisions.select('retry_count', 'none', actor_id='maya', expected_version=prior.version,
                             tick=service.clock.now, command_id='revise', correlation_id='payment',
                             grant_id='grant.retry_count', reason='later policy')
    engine.step()
    assert engine.observations[0].payload['decision_refs'] == [d.ref.as_dict() for d in first.proposal.decisions]
    assert prior.selected == 'three'


@pytest.mark.parametrize('change', [dict(observation_lag=-1), dict(recovery_delay=True),
                                    dict(duplicate_probability=float('nan')), dict(mix=(1, 1, 0, 0)),
                                    dict(workload_rate=1.5), dict(retry_cost=-1), dict(recovery=(1, 0, 0))])
def test_invalid_world_boundaries_reject(change):
    with pytest.raises((TypeError, ValueError)):
        world(**change)


def test_invalid_or_foreign_ship_is_atomic(tmp_path):
    service, proposal = delivery(tmp_path)
    engine = PaymentOutcomes(world(), service.history, service.clock)
    before = service.history.canonical_bytes()
    for workload, candidate in [((payment(), payment()), proposal),
                                ((payment(),), replace(proposal, event_id='foreign')),
                                ((payment(),), replace(proposal, behavior=replace(proposal.behavior, retry_count=0)))]:
        with pytest.raises(ValueError):
            engine.ship(candidate, workload, command_id='ship')
        assert service.history.canonical_bytes() == before and service.clock.pending_count == 0
    engine.ship(proposal, (), command_id='ship')
    with pytest.raises(ValueError, match='duplicate'):
        engine.ship(proposal, (), command_id='ship')


def test_future_fact_does_not_consume_pending_outcome(tmp_path):
    service, engine, _ = launch(tmp_path, (payment(arrival=2),))
    service.history.append(tick=9, event_type='ExternalFact', command_id='future', correlation_id='future', payload={})
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        engine.step()
    assert service.clock.pending_count == 1 and service.history.canonical_bytes() == before


def test_experiment_serializes_real_workload_and_full_trace():
    import runpy
    experiment = runpy.run_path(str(ROOT / 'experiments/paymentco_slice.py'))
    data = json.loads((ROOT / 'scenarios/paymentco/scenario.json').read_bytes())
    result, trace = experiment['run_case'](data, world(), (payment(),),
                                            strategy='safe_fixed', retain_history=True)
    assert result['metrics']['completed'] == 1
    assert trace['events'][-1]['event_type'] == 'OutcomeObserved'
    assert result['ordered_commands'][-2]['workload_hash']


def test_probability_zero_does_not_create_recovery_or_duplicate(tmp_path):
    _, engine, _ = launch(tmp_path, (payment('ambiguous'),),
                          rules=world(recovery=(0, 0, 0, 0), duplicate_probability=0),
                          choices={'retryable_types': 'all_failures', 'backoff': 'fixed', 'idempotency': 'unspecified'})
    metrics = drain(engine)
    assert metrics['completed'] == metrics['duplicate_charges'] == metrics['recovered'] == 0
    assert metrics['retry_attempts'] == 3 and metrics['abandoned'] == 1


def test_audit_mode_does_not_change_damage_and_departure_does_not_trigger_it(tmp_path):
    choices = {'retryable_types': 'all_failures', 'backoff': 'fixed', 'idempotency': 'new_key'}
    service, engine, _ = launch(tmp_path, (payment('ambiguous'),), choices=choices)
    service.knowledge.depart_actor('jin', tick=service.clock.now, command_id='depart', correlation_id='payment')
    metrics = drain(engine)
    _, no_audit, _ = launch(tmp_path, (payment('ambiguous'),), choices={**choices, 'audit_requirement': 'no_audit'})
    without = drain(no_audit)
    assert metrics['duplicate_charges'] == without['duplicate_charges'] == 1
    assert metrics['audited_attempts'] == 2 and without['audited_attempts'] == 0
    assert metrics['completed'] == without['completed'] and metrics['retry_cost'] == without['retry_cost']


def test_multiple_deployments_keep_delayed_old_observation(tmp_path):
    service, engine, first = launch(tmp_path, (payment(),))
    engine.step()
    engine.step()
    second = engine.ship(first.proposal, (payment(operation='second'),), command_id='ship-again')
    assert second.shipped_tick > first.shipped_tick
    assert drain(engine)['eligible'] == 2
    assert [o.payload['deployment'] for o in engine.observations] == [first.ref.as_dict(), second.ref.as_dict()]


@pytest.mark.parametrize('sample', [dict(arrival=-1), dict(category='unknown'), dict(hidden=1),
                                   dict(recovery=(0,)), dict(abandon=(0, 0, float('inf'), 0))])
def test_invalid_workload_boundaries_reject(sample):
    with pytest.raises((TypeError, ValueError)):
        payment(**sample)


def test_invariants_over_seeded_runs(tmp_path):
    rules = world(mix=(0.4, 0.2, 0.15, 0.25), recovery=(0.65, 0.02, 0, 0.4),
                  duplicate_probability=0.3, abandonment_probability=0.7, workload_rate=2)
    samples = generate_workload(rules, seed=3, arrival_window=10)
    service, engine, _ = launch(tmp_path, samples, rules=rules,
                                choices={'retryable_types': 'all_failures', 'backoff': 'fixed', 'idempotency': 'new_key'})
    metrics = drain(engine)
    assert metrics['eligible'] == metrics['completed'] + metrics['abandoned'] + metrics['failed'] == 20
    assert metrics['retry_cost'] == metrics['retry_attempts'] * rules.retry_cost
    assert metrics['total_attempts'] == metrics['eligible'] + metrics['retry_attempts']
    assert all(not (r.completed and r.abandoned) and 0 <= r.retry_attempts <= 3 for r in engine.results)
    assert metrics['duplicate_charges'] == sum(e.event_type == 'IncidentOccurred' for e in service.history.events)
    earlier = set()
    for event in service.history.events:
        assert all(p.event_id in earlier for p in event.parents)
        earlier.add(event.event_id)


def test_experiment_monitoring_control_compares_physical_results():
    import runpy
    experiment = runpy.run_path(str(ROOT / 'experiments/paymentco_slice.py'))
    protocol = json.loads(experiment['PROTOCOL'].read_bytes())
    protocol.update(seeds=[0], worlds=['world_a'])
    result, traces = experiment['collect'](protocol)
    assert result['failed_controls'] == []
    assert traces['traces']['world_a/seed-0/unsafe_fixed'] != traces['traces']['world_a/seed-0/fast_monitoring']


def test_incident_links_only_relevant_predeployment_gaps(tmp_path):
    from agent_empires.simulation.events import CausalLink
    service, engine, deployment = launch(tmp_path, (payment('ambiguous'),),
                                         choices={'retryable_types': 'all_failures', 'backoff': 'fixed', 'idempotency': 'new_key'})
    pinned = next(d for d in deployment.proposal.decisions if d.decision_id == 'idempotency')
    deployment_sequence = next(e.sequence for e in service.history.events if e.event_id == deployment.event_id)
    service.history.append(tick=service.clock.now, event_type='AssumptionMade', command_id='late-gap',
                           correlation_id='payment', entities=(pinned.ref,),
                           payload={'missing_information': ['invented after deployment']},
                           parents=(CausalLink(pinned.event_id, 'association'),))
    drain(engine)
    incident = next(e for e in service.history.events if e.event_type == 'IncidentOccurred')
    events = {e.event_id: e for e in service.history.events}
    assert incident.payload['information_gaps']
    assert all(events[g['event_id']].sequence < deployment_sequence
               and pinned.ref in events[g['event_id']].entities for g in incident.payload['information_gaps'])


def test_experiment_refuses_overwrite_detects_tampering_and_checks_fresh_budget(tmp_path, monkeypatch):
    import runpy
    experiment = runpy.run_path(str(ROOT / 'experiments/paymentco_slice.py'))
    protocol = json.loads(experiment['PROTOCOL'].read_bytes())
    protocol.update(seeds=[0], worlds=['world_a'])
    directory = tmp_path / 'evidence'
    experiment['author'](directory, protocol)
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(FileExistsError, match='overwrite'):
        experiment['author'](directory, protocol)
    assert before == {p.name: p.read_bytes() for p in directory.iterdir()}
    # Test the real CLI verification path with a small separately authored protocol.
    small_protocol = tmp_path / 'small-protocol.json'
    small_protocol.write_text(json.dumps(protocol))
    (directory / 'protocol.json').write_bytes(small_protocol.read_bytes())
    experiment['main'].__globals__['PROTOCOL'] = small_protocol
    experiment['main'].__globals__['collect'].__globals__['PROTOCOL'] = small_protocol
    # Input manifest hashes use the canonical repository protocol, independent of this test fixture.
    monkeypatch.setattr('sys.argv', ['paymentco_slice.py', '--verify-against', str(directory)])
    experiment['main']()
    saved = json.loads((directory / 'runs.json').read_bytes())
    saved['runs']['boundary/favorable']['metrics']['completed'] = 99
    (directory / 'runs.json').write_text(json.dumps(saved))
    tampered = (directory / 'runs.json').read_bytes()
    with pytest.raises(ValueError, match='canonical evidence differs'):
        experiment['main']()
    assert (directory / 'runs.json').read_bytes() == tampered
    # A slow fresh measurement must fail even if historical timing was within budget.
    times = iter((0, 61))
    monkeypatch.setattr(experiment['time'], 'perf_counter', lambda: next(times))
    with pytest.raises(RuntimeError, match='fresh run exceeds'):
        experiment['author'](tmp_path / 'slow', protocol)


def test_out_of_range_large_integer_is_rejected_as_invalid_world():
    with pytest.raises(ValueError, match='probability'):
        world(duplicate_probability=10 ** 400)


def test_world_accepts_probability_rounding_allowed_by_scenario(tmp_path):
    data = json.loads((ROOT / 'scenarios/paymentco/scenario.json').read_text())
    parameter = next(p for p in data['parameters'] if p['parameter_id'] == 'a.transient_mix')
    parameter['value'] += 5e-10
    path = tmp_path / 'rounded-scenario.json'
    path.write_text(json.dumps(data))
    checked = load_scenario(path).audit_data()
    values = {p['parameter_id']: p['value'] for p in checked['parameters']}
    mix = tuple(values[name] for name in checked['worlds'][0]['mix'].values())
    rules = world(mix=mix)
    assert len(generate_workload(rules, seed=0, arrival_window=1)) == 1
