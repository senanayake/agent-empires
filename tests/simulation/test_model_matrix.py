"""Behavioral gate checks against observed outcomes, not narrative assertions."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments import model_matrix as matrix
from agent_empires.simulation.outcomes import PaymentInput, WorldRules, generate_workload


@pytest.fixture
def inputs():
    return json.loads(matrix.INPUT.read_bytes()), matrix.load_protocol()


def soft_world(recovery=1):
    return WorldRules('soft-boundary', (0, 1, 0, 0), (0, recovery, 0, 0), 0, 1, 0.5, 5, 1, 1)


def soft_samples(count=4, abandoned=None):
    return tuple(PaymentInput(f'p{i}', 0, 'soft_decline', 0, (0.5,) * 3,
        ((0 if abandoned is None or i < abandoned else 0.9),) * 4) for i in range(count))


def test_feedback_reverses_recommendation_on_observed_world_response(inputs):
    data, protocol = inputs
    workload = soft_samples()
    bad = matrix.policy_probes(data, soft_world(0), workload)
    good = matrix.policy_probes(data, soft_world(1), workload)
    assert bad['recommendation'] == 'do_not_retry'
    assert good['recommendation'] == 'soft_only'
    assert bad['workload_sha256'] == good['workload_sha256']


@pytest.mark.parametrize('strategy', ['infer', 'clarify', 'feedback'])
def test_entire_roster_kind_has_no_effect_at_matched_state(inputs, strategy):
    data, protocol = inputs
    rules = soft_world()
    agent = matrix.run_arm(data, rules, soft_samples(), strategy, protocol, kind='agent')
    human = matrix.run_arm(data, rules, soft_samples(), strategy, protocol, kind='human')
    assert matrix.matched_projection(agent) == matrix.matched_projection(human)
    assert agent['closure'] == 6
    assert agent['authority_gaps'] > 0


def test_learning_loops_change_distinct_objects_and_preserve_history(inputs):
    data, protocol = inputs
    run = matrix.run_arm(data, soft_world(), soft_samples(), 'feedback', protocol)
    loops = {r['loop']: r for r in run['learning_records']}
    assert set(loops) == {'implementation', 'requirement', 'policy'}
    assert loops['implementation']['before']['entity_type'] == 'change_proposal'
    assert loops['requirement']['before']['entity_id'] == 'idempotency'
    assert loops['policy']['before']['entity_id'] == 'declined_handling'
    assert run['old']['fitness']['status'] == 'fail'
    assert run['future']['fitness']['status'] == 'pass'
    assert run['policy_support_at_revision'] == 'none'
    assert run['evidence_changes'] == 1
    assert run['history_prefix_unchanged']
    assert run['old']['decision_refs'] != run['future']['decision_refs']


def test_clarification_cost_and_claim_are_separate_from_authority_and_evidence(inputs):
    data, protocol = inputs
    infer = matrix.run_arm(data, soft_world(), soft_samples(), 'infer', protocol)
    clarify = matrix.run_arm(data, soft_world(), soft_samples(), 'clarify', protocol)
    assert clarify['idempotency'] == 'stable_key'
    assert clarify['channel_cost'] == 2
    assert clarify['old']['ship_tick'] > infer['old']['ship_tick']
    assert infer['evidence_changes'] == clarify['evidence_changes'] == 0
    assert infer['authority_gaps'] == clarify['authority_gaps']


@pytest.mark.parametrize('count,abandoned,status', [(0, 0, 'pending'), (3, 3, 'pending'),
    (10, 1, 'pass'), (10, 2, 'unknown'), (10, 3, 'fail')])
def test_analytical_fitness_boundaries(inputs, count, abandoned, status):
    data, protocol = inputs
    run = matrix.run_arm(data, soft_world(), soft_samples(count, abandoned), 'infer', protocol)
    assert run['old']['fitness']['status'] == status
    assert run['old']['metrics']['duplicate_charges'] == 0


def test_incomplete_and_shared_feedback_do_not_manufacture_learning(inputs):
    data, protocol = inputs
    run = matrix.run_arm(data, soft_world(), soft_samples(), 'feedback', protocol)
    sensitivity = run['assessment_sensitivity']
    assert all(r['status'] == 'pending' for r in sensitivity if r['structure'] == 'missing_last')
    assert all(r['sample_count'] == 1 for r in sensitivity if r['structure'] == 'copied_first')
    assert all(r['status'] == 'pending' for r in sensitivity if r['minimum'] >= 4 and r['structure'] == 'copied_first')


def test_harm_is_exposure_dependent_and_stable_keys_protect_autonomy(inputs):
    data, protocol = inputs
    rules = WorldRules('ambiguous', (0, 0, 0, 1), (0, 0, 0, 1), 1, 1, 0, 5, 1, 1)
    workload = (PaymentInput('p', 0, 'ambiguous', 0, (0,) * 3, (0.9,) * 4),)
    unsafe = matrix.run_arm(data, rules, workload, 'infer', protocol, kind='human')
    safe = matrix.run_arm(data, rules, workload, 'clarify', protocol)
    empty = matrix.run_arm(data, rules, (), 'infer', protocol)
    assert unsafe['old']['metrics']['duplicate_charges'] == 1
    assert safe['old']['metrics']['duplicate_charges'] == 0
    assert safe['old']['metrics']['completed'] == 1
    assert empty['old']['metrics']['duplicate_charges'] == 0
    assert empty['old']['fitness']['status'] == 'pending'


def test_repeat_retains_failed_seeds_ranges_and_fixed_samples(inputs):
    _, protocol = inputs
    protocol = {**protocol, 'seeds': [0, 1]}
    first = matrix.collect(protocol)
    assert first == matrix.collect(protocol)
    assert first['failed_controls'] == []
    assert len(first['pairs']) == 4
    for pair in first['pairs'].values():
        assert len({r['workload_sha256'] for r in pair['arms'].values()}) == 1
        assert pair['readiness']['workload_sha256'] == pair['monitoring']['workload_sha256'] == pair['arms']['feedback']['workload_sha256']
    assert first['analysis']['world_b']['future_fitness']['pass'] < 2
    assert first['analysis']['world_b']['abandonment_difference']['min'] <= first['analysis']['world_b']['abandonment_difference']['max']


def test_author_verify_refusal_tamper_and_fresh_budget(inputs, tmp_path, monkeypatch):
    _, protocol = inputs
    protocol = {**protocol, 'seeds': [0]}
    matrix.author(tmp_path, protocol)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    matrix.verify(tmp_path, protocol)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(FileExistsError):
        matrix.author(tmp_path, protocol)
    results = json.loads((tmp_path / 'results.json').read_bytes())
    results['failed_controls'].append('tampered')
    (tmp_path / 'results.json').write_text(json.dumps(results))
    with pytest.raises(ValueError, match='results.json'):
        matrix.verify(tmp_path, protocol)
    (tmp_path / 'results.json').write_bytes(before['results.json'])
    ticks = iter([0, 121])
    monkeypatch.setattr(matrix.time, 'perf_counter', lambda: next(ticks))
    with pytest.raises(RuntimeError, match='budget'):
        matrix.verify(tmp_path, protocol)
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_recommendation_refuses_unpaired_observations():
    with pytest.raises(ValueError, match='paired'):
        matrix.recommend_policy([{'operation_id': 'a', 'abandoned': True}], [])


def test_successful_autonomy_preserves_recognized_authority(inputs):
    data, protocol = inputs
    run = matrix.run_arm(data, soft_world(), soft_samples(), 'feedback', protocol,
                         kind='agent', preserve_authority=True)
    assert run['authority_gaps'] == 0
    assert run['future']['fitness']['status'] == 'pass'
    assert run['policy_support_at_revision'] == 'none'
