"""Counterexamples and bounded accounting for a diagnostic with no damage authority."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

from agent_empires.simulation.metrics import (
    AssumptionExposure, assumption_components, candidate_product, assumption_debt,
)

ROOT = Path(__file__).resolve().parents[2]


def exposure(**changes):
    values = dict(assumption_id='idempotency@1', uncertainty=1, impact=1,
                  propagated_to=('proposal@1',), created_tick=0, reversibility=0,
                  source_ids=('interface-gap',))
    values.update(changes)
    return AssumptionExposure(**values)


def components(record=None, **changes):
    args = dict(now_tick=16, age_window=16, propagation_limit=1)
    args.update(changes)
    return assumption_components(record or exposure(), **args)


@pytest.mark.parametrize('field', ['uncertainty', 'impact', 'reversibility'])
@pytest.mark.parametrize('bad', [-0.01, 1.01, float('nan'), float('inf'), True, '1', 10**1000])
def test_invalid_normalized_units_are_rejected(field, bad):
    with pytest.raises(ValueError):
        exposure(**{field: bad})


@pytest.mark.parametrize('field', ['uncertainty', 'impact'])
def test_zero_factor_and_full_boundary(field):
    assert candidate_product(components(exposure(**{field: 0}))) == 0
    assert candidate_product(components()) == 1


def test_age_saturates_without_expiring_history_and_resolution_freezes_age():
    row = exposure(resolved_tick=8)
    assert components(now_tick=0).persistence == 0
    assert components(now_tick=8).persistence == 0.5
    assert components(now_tick=16).persistence == 1
    assert components(now_tick=1600).persistence == 1
    assert components(row, now_tick=1600).persistence == 0.5
    assert components(row, now_tick=4).persistence == 0.25


@pytest.mark.parametrize('args', [dict(now_tick=-1), dict(now_tick=True),
    dict(age_window=0), dict(age_window=1.5), dict(propagation_limit=0),
    dict(propagation_limit=True)])
def test_invalid_windows_and_time_rejected(args):
    with pytest.raises((ValueError, TypeError)):
        components(**args)
    with pytest.raises(ValueError):
        components(exposure(created_tick=17))


@pytest.mark.parametrize('changes', [dict(created_tick=-1), dict(resolved_tick=-1),
    dict(created_tick=4, resolved_tick=3), dict(propagated_to=['mutable']),
    dict(propagated_to=('',)), dict(source_ids=['mutable']), dict(assumption_id='')])
def test_invalid_record_rejected(changes):
    with pytest.raises(ValueError):
        exposure(**changes)


def test_unique_propagation_not_paths_messages_or_traffic():
    row = exposure(propagated_to=('a@1', 'a@1', 'a@1', 'b@1'))
    assert components(row, propagation_limit=4).propagation == 0.5
    assert components(row, propagation_limit=1).propagation == 1
    assert components(exposure(propagated_to=())).propagation == 0
    assert components(replace(row, propagated_to=tuple(reversed(row.propagated_to)))) == components(row)


def test_correlated_transitive_roots_do_not_multiply_conservative_total():
    a = exposure(assumption_id='a', source_ids=('x',))
    b = exposure(assumption_id='b', source_ids=('x', 'y'), impact=0.5)
    c = exposure(assumption_id='c', source_ids=('y',))
    args = dict(now_tick=16, age_window=16, propagation_limit=1)
    report = assumption_debt((a, b, c, a), **args)
    assert report.naive_total == 2.5
    assert report.grouped_total == 1
    assert report.groups == (('a', 'b', 'c'),)
    assert assumption_debt((c, a, b), **args) == report
    assert assumption_debt((), **args).grouped_total == 0
    assert assumption_debt((replace(a, source_ids=()), replace(c, source_ids=())), **args).grouped_total == 2
    with pytest.raises(ValueError, match='conflicting'):
        assumption_debt((a, replace(a, impact=0)), **args)


def test_reversible_low_impact_and_product_collisions_remain_inspectable():
    low = components(exposure(impact=0.05, reversibility=1))
    assert candidate_product(low) == 0.05
    assert low.reversibility == 1
    assert candidate_product(low, adjust_reversibility=True) == 0
    first = components(exposure(impact=0.25, uncertainty=1))
    second = components(exposure(impact=1, uncertainty=0.25))
    assert first != second
    assert candidate_product(first) == candidate_product(second)


def test_monotonicity_and_scale_choices_are_explicit():
    row = exposure(propagated_to=('a',))
    assert candidate_product(components(row, propagation_limit=4)) <= candidate_product(components(row))
    assert candidate_product(components(row, age_window=64)) <= candidate_product(components(row))
    assert candidate_product(components(exposure(impact=0.2))) < candidate_product(components(exposure(impact=0.4)))


def load_experiment():
    spec = importlib.util.spec_from_file_location('ae014', ROOT / 'experiments/assumption_debt_ablation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_high_debt_does_not_create_incident_and_zero_age_does_not_prevent_one():
    experiment = load_experiment()
    cases = experiment.boundary_cases()
    assert cases['harmful']['metrics']['duplicate_charges'] == 1
    assert cases['no_traffic']['metrics']['duplicate_charges'] == 0
    assert cases['transient']['metrics']['duplicate_charges'] == 0
    assert cases['protected']['metrics']['duplicate_charges'] == 0
    assert cases['harmful']['components'] == cases['no_traffic']['components']
    assert cases['harmful']['scores']['product'] == 1
    assert cases['newborn_harm']['scores']['product'] == 0
    assert cases['newborn_harm']['metrics']['duplicate_charges'] == 1
    assert all(case['diagnostic_preserved_history'] for case in cases.values())


def test_cli_replays_without_overwrite_and_rejects_tamper(tmp_path):
    script = ROOT / 'experiments/assumption_debt_ablation.py'
    authored = tmp_path / 'evidence'
    def run(flag):
        return subprocess.run([sys.executable, str(script), flag, str(authored)],
                              capture_output=True, text=True, timeout=60)
    result = run('--output-dir')
    assert result.returncode == 0, result.stderr
    before = {p.name: p.read_bytes() for p in authored.iterdir()}
    result = run('--verify-against')
    assert result.returncode == 0, result.stderr
    assert before == {p.name: p.read_bytes() for p in authored.iterdir()}
    assert run('--output-dir').returncode != 0
    (authored / 'results.json').write_text('{}\n')
    assert run('--verify-against').returncode != 0
