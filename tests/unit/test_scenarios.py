"""Authoring boundaries and access projections, using the real PaymentCo input."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from agent_empires.application.scenarios import ScenarioError, load_scenario

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'scenarios/paymentco/scenario.json'


@pytest.fixture
def data():
    return json.loads(INPUT.read_text())


def load_changed(tmp_path, data):
    path = tmp_path / 'scenario.json'
    path.write_text(json.dumps(data))
    return load_scenario(path)


def test_valid_load_and_content_identity():
    scenario = load_scenario(INPUT)
    assert scenario.sha256 == hashlib.sha256(INPUT.read_bytes()).hexdigest()
    assert len(scenario.audit_data()['actors']) == 10
    assert len(scenario.audit_data()['decisions']) == 6
    assert len(scenario.audit_data()['worlds']) == 2
    assert scenario.snapshot_for('sarah')['knowledge']


@pytest.mark.parametrize('change,match', [
    (lambda d: d['holdings'][0]['holder'].update(holder_id='missing'), 'holder'),
    (lambda d: d['actors'].append(copy.deepcopy(d['actors'][0])), 'duplicate'),
    (lambda d: d['parameters'][0].update(value=1.1), 'range'),
    (lambda d: d['parameters'][0].update(value=True), 'number'),
    (lambda d: d['parameters'][0].update(value=float('nan')), 'finite|JSON'),
    (lambda d: d['parameters'][0].update(unit='seconds'), 'unit'),
    (lambda d: d.update(schema_version=2), 'version|enum'),
    (lambda d: d.update(model_version='future'), 'version|enum'),
    (lambda d: d['profiles'][0]['preferences'][0]['options'].append('infinite'), 'option|preference'),
    (lambda d: d['policies'][0].update(actor_id='jin'), 'authority'),
    (lambda d: d['policies'][0].update(grant_id='missing'), 'grant|authority'),
    (lambda d: d['grants'][0].update(scope='backoff'), 'option|authority|scope'),
    (lambda d: d['holdings'][0].update(item_version=2), 'version'),
    (lambda d: d['parameters'][0].update(assumption_id='MA-99'), 'assumption|enum'),
    (lambda d: d['parameters'][0].pop('source'), 'source|required'),
    (lambda d: d['parameters'][0].update(calibration_version='study'), 'calibration|enum'),
    (lambda d: d['worlds'][0]['mix'].update(transient='unknown'), 'parameter'),
    (lambda d: d['channels'][0].update(sender='missing'), 'actor|endpoint'),
    (lambda d: d.update(hidden_answer='yes'), 'unknown|additional'),
])
def test_reject_invalid_inputs(tmp_path, data, change, match):
    change(data)
    with pytest.raises(ScenarioError, match=match):
        load_changed(tmp_path, data)


def test_hash_mismatch_rejected():
    with pytest.raises(ScenarioError, match='hash'):
        load_scenario(INPUT, expected_hash='0' * 64)


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / 'duplicate.json'
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ScenarioError, match='duplicate'):
        load_scenario(path)


def test_yaml_tags_and_non_json_are_rejected(tmp_path):
    path = tmp_path / 'scenario.yaml'
    path.write_text('!!python/object/apply:os.system [echo nope]')
    with pytest.raises(ScenarioError, match='JSON'):
        load_scenario(path)


def test_snapshot_redaction_fixture():
    scenario = load_scenario(INPUT)
    snapshot = scenario.snapshot_for('jin')
    expected = json.loads((ROOT / 'scenarios/paymentco/jin-snapshot.json').read_text())
    assert snapshot == expected
    text = json.dumps(snapshot)
    assert 'historical_scope' not in text
    assert 'recovery' not in text
    assert 'worlds' not in snapshot
    assert 'policies' not in snapshot
    assert 'profiles' not in snapshot
    assert 'functions' not in snapshot
    assert 'decline_policy' not in text
    assert 'historical_scope' in json.dumps(scenario.snapshot_for('sarah'))
    with pytest.raises(ScenarioError, match='actor'):
        scenario.snapshot_for('missing')


def test_private_world_changes_do_not_change_actor_knowledge(tmp_path, data):
    before = load_scenario(INPUT)
    data['worlds'].reverse()
    for p in data['parameters']:
        if p['parameter_id'] == 'a.transient_recovery':
            p['value'] = 0.2
    after = load_changed(tmp_path, data)
    assert before.sha256 != after.sha256
    for actor in data['actors']:
        assert before.snapshot_for(actor['actor_id']) == after.snapshot_for(actor['actor_id'])


def test_kind_relabeling_confers_no_access(tmp_path, data):
    before = load_scenario(INPUT)
    for actor in data['actors']:
        actor['kind'] = 'agent'
    after = load_changed(tmp_path, data)
    for actor in data['actors']:
        assert before.snapshot_for(actor['actor_id'])['knowledge'] == after.snapshot_for(actor['actor_id'])['knowledge']


def test_detached_audit_and_snapshot(tmp_path, data):
    scenario = load_changed(tmp_path, data)
    scenario.audit_data()['holdings'].clear()
    scenario.snapshot_for('jin')['knowledge'].clear()
    assert scenario.snapshot_for('jin')['knowledge']


def test_inaccessible_and_unheld_items_stay_private(tmp_path, data):
    data['holdings'][0]['accessible'] = False
    scenario = load_changed(tmp_path, data)
    item_id = data['holdings'][0]['item_id']
    assert all(k['item']['item_id'] != item_id for k in scenario.snapshot_for('maya')['knowledge'])
    data['holdings'] = [h for h in data['holdings'] if h['item_id'] != item_id]
    scenario = load_changed(tmp_path, data)
    assert all(k['item']['item_id'] != item_id for a in data['actors'] for k in scenario.snapshot_for(a['actor_id'])['knowledge'])


def test_profiles_share_policy_interface(tmp_path, data):
    for profile in data['profiles']:
        data['actors'][7]['profile_id'] = profile['profile_id']
        scenario = load_changed(tmp_path, data)
        option, holdings = scenario.profile_for('jin', 'retry_count').propose(
            scenario.question_for('retry_count'), scenario.knowledge_for('jin'))
        assert option in scenario.question_for('retry_count').alternatives
        assert set(holdings) <= {k['holding']['holding_id'] for k in scenario.snapshot_for('jin')['knowledge']}


@pytest.mark.parametrize('change,match', [
    (lambda d: d['policies'][0].update(option='infinite'), 'option'),
    (lambda d: d['grants'][4].update(options=['soft_only']), 'authority'),
    (lambda d: d['actors'][0].update(profile_id='missing'), 'profile'),
    (lambda d: d['holdings'][0].update(source_ids=['missing']), 'source'),
    (lambda d: d['artifacts'][0].update(reader_ids=['missing']), 'actor'),
    (lambda d: d['worlds'][0]['mix'].update(transient='a.hard_mix'), 'sum'),
    (lambda d: d['parameters'][0].update(sensitivity_range=[-1, 1]), 'range'),
    (lambda d: d['parameters'][0].update(value=-0.1), 'range'),
    (lambda d: d.update(scenario_version='2.0.0'), 'version|pattern'),
])
def test_reference_and_boundary_rejections(tmp_path, data, change, match):
    change(data)
    with pytest.raises(ScenarioError, match=match):
        load_changed(tmp_path, data)


def test_utf8_only(tmp_path):
    path = tmp_path / 'utf16.json'
    path.write_bytes(INPUT.read_text().encode('utf-16'))
    with pytest.raises(ScenarioError, match='UTF-8|JSON'):
        load_scenario(path)


def test_goal_parameters_are_visible_without_world_parameters():
    snapshot = load_scenario(INPUT).snapshot_for('jin')
    assert snapshot['goal_parameters']['goal.target']['value'] == 0.1
    assert snapshot['goal_parameters']['goal.window']['unit'] == 'ticks'
    assert set(snapshot['goal_parameters']) == {'goal.target', 'goal.window'}


def test_explicit_artifact_readers_and_personal_access(tmp_path, data):
    data['artifacts'][0]['reader_ids'] = ['jin']
    scenario = load_changed(tmp_path, data)
    assert 'unread_incident' in {k['item']['item_id'] for k in scenario.snapshot_for('jin')['knowledge']}
    assert 'unread_incident' not in {k['item']['item_id'] for k in scenario.snapshot_for('sarah')['knowledge']}


def test_probability_boundaries_and_zero_workload(tmp_path, data):
    for p in data['parameters']:
        if p['parameter_id'].endswith('_recovery'):
            p['value'] = 0 if 'hard_decline' in p['parameter_id'] else 1
        if p['parameter_id'].endswith('.workload'):
            p['value'] = 0
    scenario = load_changed(tmp_path, data)
    assert scenario.audit_data()['worlds']


def test_fresh_simulation_owner_after_departure():
    from agent_empires.simulation.events import EventHistory
    scenario = load_scenario(INPUT)
    store = scenario.instantiate_knowledge(EventHistory('scenario-access-test'))
    assert store.view_for('sarah').lookup('historical_scope', 1)
    store.depart_actor('sarah', tick=1, command_id='depart', correlation_id='access')
    assert store.view_for('sarah').entries == ()
    assert store.view_for('jin').lookup('historical_scope', 1) is None
    # Owner is a fresh initial setup; it does not reuse another run's departed state.
    assert scenario.instantiate_knowledge(EventHistory('fresh')).view_for('sarah').lookup('historical_scope', 1)


def test_oversized_integer_rejected_as_scenario_error(tmp_path, data):
    data['parameters'][0]['value'] = 10 ** 400
    with pytest.raises(ScenarioError, match='range'):
        load_changed(tmp_path, data)


def test_schema_expansion_is_not_silently_ignored(tmp_path, monkeypatch):
    from agent_empires.application import scenarios
    schema = json.loads(scenarios.SCHEMA_PATH.read_text())
    schema['properties']['scenario_version']['format'] = 'unimplemented-format'
    path = tmp_path / 'schema.json'
    path.write_text(json.dumps(schema))
    monkeypatch.setattr(scenarios, 'SCHEMA_PATH', path)
    with pytest.raises(ScenarioError, match='unsupported schema keyword'):
        load_scenario(INPUT)


def test_supported_assertion_next_to_schema_reference_is_enforced(tmp_path, monkeypatch):
    from agent_empires.application import scenarios
    schema = json.loads(scenarios.SCHEMA_PATH.read_text())
    # An allowed assertion added to an existing reference must not disappear.
    schema['properties']['actors']['items']['enum'] = [{'actor_id': 'different'}]
    path = tmp_path / 'schema.json'
    path.write_text(json.dumps(schema))
    monkeypatch.setattr(scenarios, 'SCHEMA_PATH', path)
    with pytest.raises(ScenarioError, match='enum'):
        load_scenario(INPUT)
