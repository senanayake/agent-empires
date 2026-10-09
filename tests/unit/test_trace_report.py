"""Ordering, access boundaries and observed-versus-inferred explanation tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('trace_report', ROOT / 'experiments/trace_report.py')
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)
SOURCE = ROOT / 'research/experiments/AE-010/causal-traces.json'


def event(number, kind='PrivateFact', payload=None, parents=(), tick=0):
    return dict(event_id=f'e{number}', sequence=number, tick=tick, event_type=kind,
                schema_version=1, command_id='private-command', correlation_id='private-run',
                entities=[], payload=payload or {},
                parents=[dict(event_id=f'e{n}', relation=relation) for n, relation in parents])


def history(*events):
    return dict(history_schema_version=1, run_id='private-run', events=list(events))


def decision(support='none'):
    return event(0, 'DecisionSelected', dict(decision_id='idempotency', version=1,
        selected='new_key', authority_basis='inferred_without_authority',
        support=support, confidence='high', missing_information=['SECRET-PROPOSITION'],
        rationale=['SECRET-RATIONALE'], reason='SECRET-REASON', evidence=[]))


def actual(case='boundary/harmful_human'):
    return json.loads(SOURCE.read_text())['traces'][case]


def test_shared_multiple_parents_order_once_and_keep_relation_types():
    graph = history(event(0), event(1, parents=((0, 'direct_cause'),)),
                    event(2, parents=((0, 'supporting_evidence'),)),
                    event(3, parents=((2, 'association'), (1, 'direct_cause'))))
    shuffled = deepcopy(graph)
    shuffled['events'].reverse()
    before = deepcopy(shuffled)
    selected = report.causal_events(shuffled, ['e3', 'e2'])
    assert [e['event_id'] for e in selected] == ['e0', 'e1', 'e2', 'e3']
    assert selected[-1]['parents'] == graph['events'][-1]['parents']
    assert report.causal_events(shuffled, ['e2', 'e3']) == selected
    assert shuffled == before


def test_unknown_roots_and_empty_roots():
    with pytest.raises(ValueError, match='unknown root'):
        report.causal_events(history(event(0)), ['missing'])
    assert report.causal_events(history(event(0)), []) == []


@pytest.mark.parametrize('graph', [
    history(event(0, parents=((9, 'direct_cause'),))),
    history(event(0, parents=((1, 'direct_cause'),)), event(1)),
    history(event(0), event(0)),
    history(event(0, parents=((0, 'direct_cause'),))),
    history(event(0), event(1, parents=((0, 'made_up'),))),
])
def test_invalid_history_rejected_before_reporting(graph):
    with pytest.raises(ValueError):
        report.causal_events(graph, ['e0'])


def test_hidden_payload_metadata_and_unknown_types_cannot_leak():
    private = event(1, 'KnowledgeHoldingRecorded', dict(item={'proposition': 'HIDDEN-FACT'},
        holding={'accessible': True, 'holder': {'holder_id': 'someone_else'}}))
    private['event_id'] = 'HIDDEN-EVENT-ID'
    public = event(2, 'WorkStarted', {'actor_id': 'jin', 'defect_injection': 'SECRET-DEFECT'}, tick=1)
    public['parents'] = [dict(event_id=private['event_id'], relation='association')]
    graph = history(decision(), private, public)
    output = report.render_trace(graph, view='player', at_tick=1)
    for secret in ('SECRET', 'HIDDEN', 'private-command', 'private-run', 'someone_else'):
        assert secret not in output
    mutated = deepcopy(graph)
    mutated['events'][0]['payload']['reason'] = 'DIFFERENT SECRET'
    mutated['events'][1]['payload']['item']['proposition'] = 'DIFFERENT HIDDEN WORLD'
    assert report.render_trace(mutated, view='player', at_tick=1) == output
    assert 'HIDDEN-FACT' in report.render_trace(graph, view='audit', at_tick=1)
    assert 'association: unavailable antecedent' in output


def test_absent_support_and_conflict_do_not_become_proven_wrong():
    missing = report.render_trace(history(decision()), at_tick=0)
    conflict = report.render_trace(history(decision('conflicted')), at_tick=0)
    assert 'evidence support: none' in missing
    assert 'evidence support: conflicted' in conflict
    assert 'authority: inferred without authority' in missing
    for output in (missing, conflict):
        assert 'proven wrong' not in output.lower()
        assert 'incorrect' not in output.lower()
    failed = event(1, 'VerificationCompleted', {'assessments': [
        {'dimension': 'requirement_conformance', 'status': 'fail', 'method': 'private'}]})
    assert 'requirement conformance: fail' in report.render_trace(history(decision(), failed), at_tick=0)


def test_actual_feedback_is_unavailable_until_observed_and_no_world_leak():
    graph = actual()
    before = report.render_trace(graph, at_tick=7)
    after = report.render_trace(graph, at_tick=8)
    assert 'Observation received' not in before
    assert 'duplicate charges: 1' not in before
    assert 'Observation received' in after and 'duplicate charges: 1' in after
    for output in (before, after):
        for private in ('operation_committed', 'IncidentOccurred', 'PaymentOutcome',
                        'world_id', 'new_key', 'unvalidated-world', 'proposition', 'ae010-payment'):
            assert private not in output
    benign = report.render_trace(actual('boundary/harmless_unsupported'), at_tick=8)
    assert 'evidence support: none' in benign and 'duplicate charges: 0' in benign
    assert 'evidence support: none' in after  # outcomes do not rewrite justification


def test_unseen_root_rejected_and_cutoff_is_integer():
    graph = actual()
    observed = graph['events'][-1]['event_id']
    with pytest.raises(ValueError, match='unavailable root'):
        report.render_trace(graph, roots=[observed], at_tick=7)
    hidden = graph['events'][0]['event_id']
    with pytest.raises(ValueError, match='unavailable root'):
        report.render_trace(graph, roots=[hidden], at_tick=8)
    for cutoff in (-1, True, 0.5):
        with pytest.raises(ValueError):
            report.render_trace(graph, at_tick=cutoff)


def test_packet_reproducible_separate_audit_and_refuses_overwrite(tmp_path):
    first, second = tmp_path / 'first', tmp_path / 'second'
    report.author_packet(SOURCE, first)
    report.author_packet(SOURCE, second)
    files = sorted(p.relative_to(first) for p in first.rglob('*') if p.is_file())
    assert files
    for relative in files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
    reader = (first / 'reader/case-A-after.md').read_text()
    assert 'duplicate charges: 1' in reader and 'operation_committed' not in reader
    audit = json.loads((first / 'audit/case-A.json').read_text())
    assert any(e['event_type'] == 'IncidentOccurred' for e in audit['events'])
    with pytest.raises(FileExistsError):
        report.author_packet(SOURCE, first)
    assert not list((first / 'reader').glob('*response*'))  # template is not data


def test_cli_generates_and_verifies_without_overwriting_and_detects_tamper(tmp_path):
    destination = tmp_path / 'packet'
    command = [sys.executable, str(ROOT / 'experiments/trace_report.py'), '--source', str(SOURCE)]
    made = subprocess.run(command + ['--packet-dir', str(destination)], capture_output=True, text=True)
    assert made.returncode == 0, made.stderr
    before = (destination / 'reader/case-A-after.md').read_bytes()
    checked = subprocess.run(command + ['--verify-against', str(destination)], capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    assert (destination / 'reader/case-A-after.md').read_bytes() == before
    (destination / 'reader/case-A-after.md').write_text('tampered')
    rejected = subprocess.run(command + ['--verify-against', str(destination)], capture_output=True, text=True)
    assert rejected.returncode != 0 and 'differs' in rejected.stderr
    assert (destination / 'reader/case-A-after.md').read_text() == 'tampered'


def test_delayed_observation_names_its_pinned_version_not_latest_choice():
    old = decision()
    new = deepcopy(old)
    new.update(event_id='e1', sequence=1, tick=1, event_type='DecisionRevised')
    new['payload'].update(version=2, selected='stable_key')
    observed = event(2, 'OutcomeObserved', dict(completed=True, abandoned=False,
        duplicate_charges=1, outcome_tick=0, decision_refs=[
            {'entity_type': 'decision', 'entity_id': 'idempotency', 'version': 1}]), tick=8)
    output = report.render_trace(history(old, new, observed), at_tick=8)
    observation_line = next(line for line in output.splitlines() if 'Observation received' in line)
    assert 'pinned choices: idempotency v1' in observation_line
    assert 'idempotency v2' not in observation_line
    assert 'Choice idempotency v2: reuse an operation key' in output


def test_all_retained_histories_render_only_observed_counts():
    traces = json.loads(SOURCE.read_text())['traces']
    for graph in traces.values():
        tick = max(e['tick'] for e in graph['events'])
        output = report.render_trace(graph, at_tick=tick)
        observed = [e for e in graph['events'] if e['event_type'] == 'OutcomeObserved']
        assert output.count('Observation received') == len(observed)
        assert 'operation_committed' not in output and 'proposition' not in output
        assert report.render_trace(graph, at_tick=tick) == output
