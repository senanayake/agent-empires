"""Finite learning changes artifacts, requirements and authorized policy separately."""
from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import pytest

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.assurance import assess_production
from agent_empires.simulation.decisions import EvidenceUse
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem
from agent_empires.simulation.learning import Learning
from agent_empires.simulation.outcomes import PaymentInput, PaymentOutcomes, WorldRules

ROOT = Path(__file__).resolve().parents[2]


def setup():
    service = DeliveryService(load_scenario(ROOT / 'scenarios/paymentco/scenario.json'), run_id='loops')
    learning = Learning(service.knowledge, service.authority, service.clock, service.history)
    return service, learning


def choose(service, name, option, *, actor='jin', grant=None):
    return service.decisions.select(name, option, actor_id=actor,
        expected_version=len(service.decisions.versions(name)), tick=service.clock.now,
        command_id=f'choose.{name}.{len(service.decisions.versions(name))}',
        correlation_id='loops', reason='authored initial interpretation', grant_id=grant)


def finish(service, command, defect=None):
    service.start('jin', command_id=command, defect=defect)
    return service.step()


def report(service, old, *, source=('independent-interface',), method='report',
           quality='usable', option='stable_key', stance='supports', freshness='current', holder='jin', suffix='1'):
    item = KnowledgeItem('report.' + suffix, 1, 'idempotency', option)
    service.knowledge.register_item(item)
    holding = KnowledgeHolding('report.' + suffix, item.ref, HolderRef('actor', holder), source,
                               'medium', freshness)
    service.knowledge.record_holding(holding, tick=service.clock.now,
                                    command_id='report.' + suffix, correlation_id='loops')
    return EvidenceUse(holding.holding_id, old.ref, option, stance, method, quality)


def policy_run(*, samples=4, abandoned=None, lag=5, arrival=0):
    service, learning = setup()
    choose(service, 'retryable_types', 'all_failures')
    choose(service, 'retry_count', 'one')
    choose(service, 'backoff', 'fixed')
    policy = choose(service, 'declined_handling', 'do_not_retry', actor='priya', grant='grant.declined_handling')
    proposal = finish(service, 'old').proposal
    world = WorldRules('authored-soft-world', (0, 1, 0, 0), (0, 1, 0, 0), 0, 1, 0.5, lag, 1, 1)
    workload = tuple(PaymentInput(f'p{i}', arrival, 'soft_decline', 0, (0, 0, 0),
        ((0 if abandoned is None or i < abandoned else 0.9),) * 4) for i in range(samples))
    engine = PaymentOutcomes(world, service.history, service.clock)
    deployment = engine.ship(proposal, workload, command_id='old.ship')
    while engine.step() is not None:
        pass
    return service, learning, policy, engine, deployment, workload


def assess(service, engine, deployment, ids=None):
    return assess_production(service.history, deployment.ref, service.goal,
        tuple(e.event_id for e in engine.observations) if ids is None else ids,
        tick=service.clock.now, command_id='assess.' + str(len(service.history.events)),
        minimum_samples=4, revision_margin=0.2)


def revise_policy(service, learning, review, **kwargs):
    return learning.revise_policy(service.decisions, 'declined_handling', 'soft_only', review,
        actor_id=kwargs.pop('actor_id', 'priya'), grant_id=kwargs.pop('grant_id', 'grant.declined_handling'),
        expected_version=kwargs.pop('expected_version', 1), command_id='policy.revise', **kwargs)


def test_implementation_fix_retains_intent_decisions_and_failing_artifact():
    service, learning = setup()
    choose(service, 'retry_count', 'three')
    bad = finish(service, 'broken', 'omit_retries')
    prefix = service.history.events
    good = finish(service, 'fixed')
    record = learning.record_implementation_fix(bad.proposal, good.proposal,
        service.behavior_parameters, command_id='learn.fix')
    assert record.before == bad.proposal.ref and record.after == good.proposal.ref
    assert bad.proposal.behavior.retry_count == 0 < good.proposal.behavior.retry_count
    assert bad.proposal.decisions == good.proposal.decisions
    assert service.history.events[:len(prefix)] == prefix
    assert record.loop == 'implementation' and record.retained == bad.proposal.decision_refs


def test_requirement_revision_from_independent_disconfirming_report_keeps_old_deployment():
    service, learning = setup()
    old = choose(service, 'idempotency', 'new_key')
    proposal = finish(service, 'unsafe').proposal
    evidence = report(service, old)
    revised = learning.revise_requirement(service.decisions, 'idempotency', 'stable_key',
        evidence=(evidence,), actor_id='jin', expected_version=1, command_id='requirement.revise')
    assert revised.version == 2 and revised.prior == old.ref and revised.support == 'supported'
    assert revised.authority_basis == 'inferred_without_authority'
    assert next(d for d in proposal.decisions if d.decision_id == 'idempotency') == old
    assert learning.records[-1].before == old.ref


@pytest.mark.parametrize('changes', [
    {'method': 'verification'}, {'quality': 'weak'}, {'freshness': 'stale'},
    {'source': ('decision:idempotency@1',)}, {'holder': 'sarah'}, {'stance': 'inconclusive'},
])
def test_repeated_weak_copied_or_inaccessible_reports_do_not_justify_revision(changes):
    service, learning = setup()
    old = choose(service, 'idempotency', 'new_key')
    evidence = tuple(report(service, old, suffix=str(i), **changes) for i in range(4))
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        learning.revise_requirement(service.decisions, 'idempotency', 'stable_key', evidence=evidence,
            actor_id='jin', expected_version=1, command_id='reject')
    assert service.history.canonical_bytes() == before
    assert service.decisions.versions('idempotency') == (old,)


def test_shared_source_disagreement_is_not_resolved_by_report_majority():
    service, learning = setup()
    old = choose(service, 'idempotency', 'new_key')
    uses = tuple(report(service, old, suffix=str(i)) for i in range(4))
    uses += (report(service, old, stance='challenges', suffix='contradiction'),)
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='conflict'):
        learning.revise_requirement(service.decisions, 'idempotency', 'stable_key', evidence=uses,
            actor_id='jin', expected_version=1, command_id='reject')
    assert service.history.canonical_bytes() == before


def test_wrong_authorized_policy_revised_and_future_deployment_observed_separately():
    service, learning, old, engine, deployed, workload = policy_run()
    review = assess(service, engine, deployed)
    assert review.assessment.status == 'fail' and review.sample_count == 4
    prefix = service.history.events
    revised = revise_policy(service, learning, review)
    assert old.grant_ref is not None and revised.grant_ref is not None
    assert revised.support == 'none'  # challenge is not proof of the replacement
    assert revised.version == 2 and old.selected == 'do_not_retry'
    future = finish(service, 'future').proposal
    new_deployment = engine.ship(future, workload, command_id='future.ship')
    while engine.step() is not None:
        pass
    new_ids = tuple(e.event_id for e in engine.observations if new_deployment.ref in e.entities)
    new_review = assess(service, engine, new_deployment, new_ids)
    assert new_review.assessment.status == 'pass'
    assert deployed.proposal.decisions != new_deployment.proposal.decisions
    assert next(d for d in deployed.proposal.decisions if d.decision_id == 'declined_handling') == old
    assert service.history.events[:len(prefix)] == prefix
    assert review.assessment.subject == deployed.ref


@pytest.mark.parametrize('samples,abandoned,status', [(0, 0, 'pending'), (1, 1, 'pending'),
    (3, 3, 'pending'), (4, 1, 'unknown'), (4, 0, 'pass')])
def test_insufficient_noisy_or_confirming_feedback_does_not_revise(samples, abandoned, status):
    service, learning, old, engine, deployed, _ = policy_run(samples=samples, abandoned=abandoned)
    review = assess(service, engine, deployed)
    assert review.assessment.status == status
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        revise_policy(service, learning, review)
    assert service.history.canonical_bytes() == before


def test_duplicate_observation_ids_do_not_count_as_more_samples():
    service, _, _, engine, deployed, _ = policy_run(samples=1)
    review = assess(service, engine, deployed, (engine.observations[0].event_id,) * 20)
    assert review.sample_count == 1 and review.assessment.status == 'pending'


def test_old_delayed_evidence_cannot_revise_a_newer_policy_version():
    service, learning, old, engine, deployed, _ = policy_run(lag=20)
    choose(service, 'declined_handling', 'soft_only', actor='priya', grant='grant.declined_handling')
    review = assess(service, engine, deployed)
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='version'):
        revise_policy(service, learning, review, expected_version=2)
    assert review.assessment.subject == deployed.ref
    assert service.history.canonical_bytes() == before


@pytest.mark.parametrize('actor,grant', [('jin', 'grant.declined_handling'), ('priya', 'grant.audit_requirement')])
def test_policy_revision_requires_current_scoped_authority(actor, grant):
    service, learning, _, engine, deployed, _ = policy_run()
    review = assess(service, engine, deployed)
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        revise_policy(service, learning, review, actor_id=actor, grant_id=grant)
    assert service.history.canonical_bytes() == before


def test_verification_and_mixed_deployment_events_cannot_supply_production_validation():
    service, _, _, engine, deployed, _ = policy_run()
    verification = next(e for e in service.history.events if e.event_type == 'VerificationCompleted')
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        assess(service, engine, deployed, (verification.event_id,) * 4)
    assert service.history.canonical_bytes() == before


@pytest.mark.parametrize('samples,abandoned,status', [(10, 3, 'fail'), (10, 1, 'pass'), (10, 2, 'unknown')])
def test_policy_rate_threshold_includes_exact_decimal_boundary(samples, abandoned, status):
    service, _, _, engine, deployed, _ = policy_run(samples=samples, abandoned=abandoned)
    assert assess(service, engine, deployed).assessment.status == status


def test_missing_observations_cannot_cherry_pick_a_goal_result():
    service, _, _, engine, deployed, _ = policy_run(samples=5, abandoned=4)
    review = assess(service, engine, deployed, tuple(e.event_id for e in engine.observations[:4]))
    assert review.sample_count == 4 and review.assessment.status == 'pending'


def test_delayed_old_feedback_arrives_after_policy_revision():
    service, learning, old, engine, deployed, workload = policy_run(lag=20)
    # Introduce a second old-policy deployment and revise the policy before
    # its feedback arrives. Do not run delivery while outcomes has tasks.
    another = engine.ship(deployed.proposal, workload, command_id='delayed.ship')
    while len(engine.results) < 8:
        engine.step()
    assert not any(another.ref in e.entities for e in engine.observations)
    reviewed = assess(service, engine, deployed, tuple(e.event_id for e in engine.observations))
    revised = revise_policy(service, learning, reviewed)
    # Existing delivery artifacts are immutable; finish after draining delayed
    # evidence, then assess it against the old version and reject misapplication.
    while engine.step() is not None:
        pass
    late = assess(service, engine, another, tuple(e.event_id for e in engine.observations
                                                if another.ref in e.entities))
    assert old.ref in late.assessment.source_dependencies and revised.ref not in late.assessment.source_dependencies
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='version'):
        learning.revise_policy(service.decisions, 'declined_handling', 'retry_all', late,
            actor_id='priya', grant_id='grant.declined_handling', expected_version=2, command_id='late.revise')
    assert service.history.canonical_bytes() == before


@pytest.mark.parametrize('change', ['rate', 'goal', 'count', 'event'])
def test_forged_production_assessment_is_rejected_without_mutation(change):
    service, learning, _, engine, deployed, _ = policy_run()
    review = assess(service, engine, deployed)
    if change == 'rate':
        review = replace(review, abandonment_rate=0.8)
    elif change == 'goal':
        review = replace(review, goal=replace(review.goal, version=2))
    elif change == 'count':
        review = replace(review, sample_count=40)
    else:
        review = replace(review, event_id=engine.observations[0].event_id)
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        revise_policy(service, learning, review)
    assert service.history.canonical_bytes() == before


def test_revoked_authority_and_stale_commands_preserve_policy_and_history():
    service, learning, old, engine, deployed, _ = policy_run()
    review = assess(service, engine, deployed)
    service.authority.revoke('grant.declined_handling', tick=service.clock.now,
                             command_id='revoke', correlation_id='loops')
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError):
        revise_policy(service, learning, review)
    assert service.history.canonical_bytes() == before
    assert service.decisions.versions('declined_handling') == (old,)


def test_copies_are_one_root_and_identical_replay_has_identical_history():
    def run(count):
        service, learning = setup()
        old = choose(service, 'idempotency', 'new_key')
        uses = tuple(report(service, old, suffix=str(i)) for i in range(count))
        revised = learning.revise_requirement(service.decisions, 'idempotency', 'stable_key',
            evidence=uses, actor_id='jin', expected_version=1, command_id='requirement.revise')
        return service, revised
    one, single = run(1)
    many, copies = run(8)
    assert single.support == copies.support == 'supported'
    assert single.backed_source_ids == copies.backed_source_ids == ('independent-interface',)
    assert many.history.canonical_bytes() == run(8)[0].history.canonical_bytes()


def test_implementation_fix_cannot_silently_change_requirement_versions():
    service, learning = setup()
    choose(service, 'retry_count', 'three')
    old = finish(service, 'broken', 'omit_retries').proposal
    choose(service, 'retry_count', 'one')
    new = finish(service, 'changed').proposal
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='same intent'):
        learning.record_implementation_fix(old, new, service.behavior_parameters, command_id='reject')
    assert service.history.canonical_bytes() == before


@pytest.mark.parametrize('minimum,margin', [(0, 0.2), (True, 0.2), (4, -0.1), (4, float('nan')), (4, True), (4, 10**1000)])
def test_invalid_update_rules_rejected_before_assessment(minimum, margin):
    service, _, _, engine, deployed, _ = policy_run()
    before = service.history.canonical_bytes()
    with pytest.raises((ValueError, TypeError)):
        assess_production(service.history, deployed.ref, service.goal,
            tuple(e.event_id for e in engine.observations), tick=service.clock.now, command_id='bad-rule',
            minimum_samples=minimum, revision_margin=margin)
    assert service.history.canonical_bytes() == before


def test_altered_decision_copies_cannot_turn_a_recorded_regression_into_a_fix():
    service, learning = setup()
    choose(service, 'retry_count', 'three')
    working = finish(service, 'working').proposal
    regression = finish(service, 'regression', 'omit_retries').proposal
    # Keep version references but substitute an interpretation in detached objects.
    # The actual recorded tests pass before the regression and fail afterwards.
    altered = tuple(replace(d, selected='none') if d.decision_id == 'retry_count' else d
                    for d in working.decisions)
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='recorded verification'):
        learning.record_implementation_fix(replace(working, decisions=altered),
            replace(regression, decisions=altered), service.behavior_parameters, command_id='false-fix')
    assert service.history.canonical_bytes() == before
    assert learning.records == ()


def test_requirement_route_cannot_bypass_authorized_policy_learning_gate():
    service, learning, old, _, _, _ = policy_run()
    item = KnowledgeItem('policy.report', 1, 'declined_handling', 'soft_only')
    service.knowledge.register_item(item)
    service.knowledge.record_holding(KnowledgeHolding('policy.report', item.ref,
        HolderRef('actor', 'jin'), ('independent-report',), 'high', 'current'),
        tick=service.clock.now, command_id='policy.report', correlation_id='loops')
    use = EvidenceUse('policy.report', old.ref, 'soft_only', 'supports', 'report', 'usable')
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='policy'):
        learning.revise_requirement(service.decisions, 'declined_handling', 'soft_only',
            evidence=(use,), actor_id='jin', expected_version=1, command_id='bypass')
    assert service.history.canonical_bytes() == before


def test_delayed_receipt_does_not_move_physical_goal_window():
    service, _, _, engine, deployed, _ = policy_run(lag=200)
    assert assess(service, engine, deployed).assessment.status == 'fail'
    service, _, _, engine, deployed, _ = policy_run(arrival=101)
    review = assess(service, engine, deployed)
    assert review.sample_count == 0 and review.assessment.status == 'pending'


def test_observations_from_two_deployments_cannot_be_pooled():
    service, _, _, engine, deployed, workload = policy_run()
    newer = engine.ship(deployed.proposal, workload, command_id='newer.ship')
    while engine.step() is not None:
        pass
    before = service.history.canonical_bytes()
    with pytest.raises(ValueError, match='deployment version'):
        assess(service, engine, newer)  # includes old deployment observations
    assert service.history.canonical_bytes() == before


def test_trace_replay_and_author_refuses_to_overwrite_evidence(tmp_path):
    directory = ROOT / 'research/experiments/AE-013'
    replay = subprocess.run([sys.executable, str(directory / 'trace_loops.py'),
                             '--verify-against', str(directory)], capture_output=True, text=True, timeout=30)
    assert replay.returncode == 0, replay.stderr
    command = [sys.executable, str(directory / 'trace_loops.py'), '--output-dir', str(tmp_path)]
    assert subprocess.run(command, capture_output=True, text=True, timeout=30).returncode == 0
    authored = (tmp_path / 'loop-traces.json').read_bytes()
    assert subprocess.run(command, capture_output=True, text=True, timeout=30).returncode != 0
    assert (tmp_path / 'loop-traces.json').read_bytes() == authored
    (tmp_path / 'loop-traces.json').write_bytes(authored + b' ')
    tampered = subprocess.run([sys.executable, str(directory / 'trace_loops.py'),
                              '--verify-against', str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert tampered.returncode != 0
    assert (tmp_path / 'loop-traces.json').read_bytes() == authored + b' '
