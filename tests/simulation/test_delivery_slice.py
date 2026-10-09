"""Delivery is executable conformance evidence, never a world truth oracle."""
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.artifacts import PaymentBehavior
from agent_empires.simulation.assurance import verify_proposal

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'scenarios/paymentco/scenario.json'


def service(tmp_path, *, profile='implementer', kind='agent', changes=None):
    data = json.loads(INPUT.read_text())
    actor = next(a for a in data['actors'] if a['actor_id'] == 'jin')
    actor.update(profile_id=profile, kind=kind)
    if changes:
        changes(data)
    path = tmp_path / 'scenario.json'
    path.write_text(json.dumps(data))
    return DeliveryService(load_scenario(path), run_id='delivery-test')


def finish(engine, *, defect=None):
    engine.start('jin', command_id='start.retry', defect=defect)
    return engine.step()


def statuses(result):
    return {a.dimension: a.status for a in result.assessments}


def test_headless_thin_work_to_green_with_explicit_gaps(tmp_path):
    engine = service(tmp_path)
    job = engine.start('jin', command_id='start.retry')
    assert job.started_tick == 0 and job.completion_tick == 1
    assert job.resource_cost == engine.spent_resource_units == 2
    assert engine.proposals == ()
    result = engine.step()
    assert result.proposal.behavior.plan('transient', 'payment-7') == (
        (1, 0, 'payment-7', 'attempt_lineage'),
        (2, 0, 'payment-7', 'attempt_lineage'),
        (3, 0, 'payment-7', 'attempt_lineage'),
    )
    assert result.proposal.behavior.plan('hard_decline', 'payment-7') == ()
    assert statuses(result) == {
        'implementation_conformance': 'pass', 'verification_status': 'pass',
        'requirement_conformance': 'unknown', 'architecture_conformance': 'unknown',
        'policy_security_conformance': 'unknown', 'validation_status': 'unknown',
        'outcome_fitness': 'unknown',
    }
    assert len(result.proposal.unsupported_decisions) == 6
    assert all(d.support == 'none' and d.authority_basis == 'inferred_without_authority'
               for d in result.proposal.decisions)
    assert not any(e.event_type == 'DeploymentCompleted' for e in engine.history.events)
    assert engine.step() is None and len(engine.proposals) == 1


def test_causal_chain_contains_required_decisions_and_pinned_assessments(tmp_path):
    engine = service(tmp_path)
    result = finish(engine)
    events = {e.event_id: e for e in engine.history.events}
    verification = next(e for e in events.values() if e.event_type == 'VerificationCompleted')
    proposal = events[verification.parents[0].event_id]
    assert proposal.event_type == 'ChangeProposalCreated'
    started = next(events[p.event_id] for p in proposal.parents
                   if events[p.event_id].event_type == 'WorkStarted')
    item = next(events[p.event_id] for p in started.parents
                if events[p.event_id].event_type == 'WorkItemCreated')
    assert events[item.parents[0].event_id].event_type == 'GoalDeclared'
    for decision in result.proposal.decisions:
        selected = events[decision.event_id]
        assert any(events[p.event_id].event_type == 'DecisionRequired' for p in selected.parents)
        assert decision.ref in proposal.entities
    assert all(a.subject == result.proposal.ref for a in result.assessments)
    assert all(a.source_dependencies == result.proposal.decision_refs for a in result.assessments)


def test_actual_implementation_defect_fails_without_reinterpreting_spec(tmp_path):
    engine = service(tmp_path)
    result = finish(engine, defect='omit_retries')
    assert result.proposal.behavior.plan('transient', 'payment') == ()
    assert next(d.selected for d in result.proposal.decisions if d.decision_id == 'retry_count') == 'three'
    assert statuses(result)['verification_status'] == 'fail'
    assert any(not check.passed for check in result.checks)
    assert statuses(result)['validation_status'] == 'unknown'


def test_unknown_dimensions_survive_authority_and_green_checks(tmp_path):
    engine = service(tmp_path)
    engine.decisions.select('retry_count', 'three', actor_id='maya', expected_version=0,
                            tick=0, command_id='authorize', correlation_id='retry',
                            grant_id='grant.retry_count', reason='authored customer trade-off')
    result = finish(engine)
    count = next(d for d in result.proposal.decisions if d.decision_id == 'retry_count')
    assert count.authority_basis == 'explicit_authorization' and count.support == 'none'
    assert count.ref in result.proposal.unsupported_decisions
    assert statuses(result)['verification_status'] == 'pass'
    assert statuses(result)['requirement_conformance'] == 'unknown'


def test_decision_revision_during_work_does_not_rewrite_proposal(tmp_path):
    engine = service(tmp_path)
    engine.start('jin', command_id='start.retry')
    engine.decisions.select('retry_count', 'one', actor_id='maya', expected_version=1,
                            tick=0, command_id='revise', correlation_id='retry',
                            grant_id='grant.retry_count', reason='revised preference')
    result = engine.step()
    assert next(d.version for d in result.proposal.decisions if d.decision_id == 'retry_count') == 1
    assert len(result.proposal.behavior.plan('transient', 'p')) == 3
    assert statuses(result)['verification_status'] == 'pass'
    assert engine.decisions.version('retry_count', 2).selected == 'one'
    with pytest.raises(FrozenInstanceError):
        result.proposal.behavior.retry_count = 0


def test_profile_speed_cost_and_actor_kind_controls(tmp_path):
    fast = service(tmp_path, kind='agent')
    matched = service(tmp_path, kind='human')
    fast_result, matched_result = finish(fast), finish(matched)
    assert fast_result == matched_result
    assert fast.history.canonical_bytes() == matched.history.canonical_bytes()
    slow = service(tmp_path, profile='human', kind='human')
    finish(slow)
    assert fast.clock.now == 1 < slow.clock.now == 5
    assert fast.spent_resource_units == 2 < slow.spent_resource_units == 5


def test_private_world_parameters_have_no_effect_on_delivery(tmp_path):
    baseline = service(tmp_path)
    def change(data):
        for parameter in data['parameters']:
            if parameter['parameter_id'] == 'a.transient_recovery':
                parameter['value'] = 0
    altered = service(tmp_path, changes=change)
    assert finish(baseline) == finish(altered)
    assert baseline.history.canonical_bytes() == altered.history.canonical_bytes()


def test_repeat_history_is_deterministic(tmp_path):
    first, second = service(tmp_path), service(tmp_path)
    assert finish(first) == finish(second)
    assert first.history.canonical_bytes() == second.history.canonical_bytes()


@pytest.mark.parametrize('dimension,option', [('retry_count', 'adaptive'),
                                             ('retryable_types', 'selected_categories')])
def test_unrefined_choices_reject_before_inference_or_charge(tmp_path, dimension, option):
    def change(data):
        preference = next(p for p in data['profiles'][1]['preferences'] if p['decision_id'] == dimension)
        preference['options'].remove(option)
        preference['options'].insert(0, option)
    engine = service(tmp_path, changes=change)
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError, match='refinement'):
        engine.start('jin', command_id='start.retry')
    assert engine.history.canonical_bytes() == before
    assert engine.spent_resource_units == 0 and engine.clock.pending_count == 0


@pytest.mark.parametrize('defect', ['unknown', True])
def test_invalid_defect_is_atomic(tmp_path, defect):
    engine = service(tmp_path)
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError, match='defect'):
        engine.start('jin', command_id='start.retry', defect=defect)
    assert engine.history.canonical_bytes() == before


def test_duplicate_start_does_not_charge_or_create_facts(tmp_path):
    engine = service(tmp_path)
    engine.start('jin', command_id='start.retry')
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError, match='duplicate'):
        engine.start('jin', command_id='start.retry')
    assert engine.history.canonical_bytes() == before and engine.spent_resource_units == 2


def test_departed_actor_cannot_start_work(tmp_path):
    engine = service(tmp_path)
    engine.knowledge.depart_actor('jin', tick=0, command_id='depart', correlation_id='retry')
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError, match='present'):
        engine.start('jin', command_id='start.retry')
    assert engine.history.canonical_bytes() == before and engine.spent_resource_units == 0


def test_executable_plan_boundaries_and_unknown_key():
    behavior = PaymentBehavior('all_failures', 3, 'fixed', 2, 8,
                               'soft_only', 'unspecified', 'summary_only')
    assert behavior.plan('soft_decline', 'p') == ((1, 2, None, 'summary_only'),
                                                (2, 4, None, 'summary_only'),
                                                (3, 6, None, 'summary_only'))
    assert behavior.plan('hard_decline', 'p') == ()
    assert replace(behavior, retry_count=0).plan('transient', 'p') == ()
    assert replace(behavior, backoff='capped_exponential').plan('ambiguous', 'p') == (
        (1, 2, None, 'summary_only'), (2, 6, None, 'summary_only'), (3, 14, None, 'summary_only'))
    assert replace(behavior, idempotency='new_key').plan('transient', 'p')[1][2] == 'p:retry:2'
    with pytest.raises(ValueError, match='category'):
        behavior.plan('unknown_failure', 'p')
    with pytest.raises(ValueError, match='nonempty'):
        behavior.plan('transient', '')
    with pytest.raises((ValueError, TypeError)):
        replace(behavior, retry_count=True)


@pytest.mark.parametrize('change', [dict(backoff='fixed', fixed_delay=9),
                                    dict(idempotency='new_key'), dict(audit='no_audit'),
                                    dict(declined_handling='retry_all', retryable_types='all_failures')])
def test_verification_detects_behavior_defects_beyond_retry_count(tmp_path, change):
    engine = service(tmp_path)
    result = finish(engine)
    broken = replace(result.proposal, behavior=replace(result.proposal.behavior, **change))
    verification = verify_proposal(broken, engine.behavior_parameters)
    assert statuses(verification)['verification_status'] == 'fail'


def test_inference_uses_live_holdings_and_access_revocation(tmp_path):
    from agent_empires.simulation.events import EntityRef
    from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem

    engine = service(tmp_path)
    claim = KnowledgeItem('runtime.count', 1, 'retry_count', 'one')
    engine.knowledge.register_item(claim)
    engine.knowledge.record_holding(
        KnowledgeHolding('runtime.count.jin', claim.ref, HolderRef('actor', 'jin'),
                         ('runtime.claim',), 'high', 'current', True, True),
        tick=0, command_id='receive', correlation_id='retry')
    engine.start('jin', command_id='first')
    assert engine.decisions.version('retry_count', 1).selected == 'one'
    # Rationale is accessible but is not automatically independent world evidence.
    assert engine.decisions.version('retry_count', 1).support == 'none'
    assert engine.decisions.version('retry_count', 1).rationale == (EntityRef('knowledge_holding', 'runtime.count.jin', 1),)
    engine.step()
    engine.knowledge.set_holding_access('runtime.count.jin', False, tick=1,
                                      command_id='revoke', correlation_id='retry')
    # A new decision question version is not invented; existing choice remains pinned.
    view = engine.knowledge.view_for('jin')
    assert engine.scenario.profile_for('jin', 'retry_count').propose(
        engine.scenario.question_for('retry_count'), view)[0] == 'three'
    engine.start('jin', command_id='second')
    assert next(d.selected for d in engine.step().proposal.decisions if d.decision_id == 'retry_count') == 'one'


@pytest.mark.parametrize('backoff,delays', [('immediate', (0, 0, 0)),
                                          ('fixed', (2, 4, 6)),
                                          ('capped_exponential', (2, 6, 14))])
def test_supported_alternative_spec_runs_and_verifies(tmp_path, backoff, delays):
    engine = service(tmp_path)
    for name, option in [('retryable_types', 'all_failures'), ('backoff', backoff),
                         ('declined_handling', 'soft_only'), ('idempotency', 'new_key'),
                         ('audit_requirement', 'summary_only')]:
        engine.decisions.select(name, option, actor_id='jin', expected_version=0,
                                tick=0, command_id='choose.' + name, correlation_id='retry',
                                reason='explicit alternate interpretation')
    result = finish(engine)
    assert statuses(result)['verification_status'] == 'pass'
    assert result.proposal.behavior.plan('soft_decline', 'p') == tuple(
        (n, delay, f'p:retry:{n}', 'summary_only') for n, delay in enumerate(delays, 1))
    assert result.proposal.behavior.plan('hard_decline', 'p') == ()


def test_zero_retries_can_be_green_without_fulfilling_the_goal(tmp_path):
    engine = service(tmp_path, profile='human', kind='human')
    result = finish(engine)
    assert all(result.proposal.behavior.plan(category, 'p') == ()
               for category in ('transient', 'ambiguous', 'soft_decline', 'hard_decline'))
    assert statuses(result)['verification_status'] == 'pass'
    assert statuses(result)['outcome_fitness'] == 'unknown'


def test_equal_time_jobs_complete_once_in_insertion_order(tmp_path):
    engine = service(tmp_path)
    engine.start('jin', command_id='first')
    engine.start('jin', command_id='second')
    assert engine.spent_resource_units == 4
    first, second = engine.step(), engine.step()
    assert [first.proposal.proposal_id, second.proposal.proposal_id] == ['proposal.first', 'proposal.second']
    assert first.proposal.completed_tick == second.proposal.completed_tick == 1
    assert engine.step() is None


def test_actor_departure_during_work_does_not_hide_admitted_cost(tmp_path):
    engine = service(tmp_path)
    engine.start('jin', command_id='start.retry')
    engine.knowledge.depart_actor('jin', tick=0, command_id='depart', correlation_id='retry')
    result = engine.step()
    assert result.proposal.resource_cost == engine.spent_resource_units == 2
    assert result.proposal.completed_tick == 1  # admitted deterministic work finishes; no cancellation rule


def test_future_fact_cannot_consume_an_earlier_pending_completion(tmp_path):
    engine = service(tmp_path)
    engine.start('jin', command_id='start.retry')
    engine.decisions.select('retry_count', 'one', actor_id='maya', expected_version=1,
                            tick=2, command_id='future.revision', correlation_id='retry',
                            grant_id='grant.retry_count', reason='external future command')
    before = engine.history.canonical_bytes()
    with pytest.raises(ValueError):
        engine.step()
    assert engine.clock.pending_count == 1
    assert engine.clock.now == 0
    assert engine.history.canonical_bytes() == before
