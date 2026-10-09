"""Strict JSON authored inputs and initial access projections for PaymentCo.

Trusted setup may inspect audit_data or instantiate_knowledge. Actor policies get
only knowledge_for/snapshot_for and a CapabilityProfile. This is an API boundary,
not a sandbox against Python introspection or malicious authors. No payment rules,
ambient randomness, inference, deployment or broadcast occurs during loading.
"""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.decisions import CapabilityProfile, DecisionQuestion
from agent_empires.simulation.events import EntityRef, EventHistory
from agent_empires.simulation.knowledge import (
    Artifact, HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / 'scenarios/paymentco/schema.json'


class ScenarioError(ValueError):
    """Invalid authored structure, provenance, reference or content identity."""


def _require(condition, message):
    if not condition:
        raise ScenarioError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def _constant(value):
    raise ScenarioError(f'JSON numbers must be finite: {value}')


def _decode(raw):
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError) as exc:
        raise ScenarioError(f'invalid JSON: {exc}') from exc


def _validate(value, rule, schema, location='$'):
    """Evaluate only the JSON Schema vocabulary used by the bundled schema.

    No remote refs, coercion, default insertion or ignored assertion keywords.
    This deliberately small evaluator is not a general JSON Schema library.
    """
    supported = {'$ref', '$schema', '$id', '$defs', 'title', 'type', 'properties',
                 'required', 'additionalProperties', 'enum', 'items', 'minItems',
                 'maxItems', 'uniqueItems', 'minLength', 'pattern', 'minimum'}
    _require(set(rule) <= supported, f'{location}: unsupported schema keyword')
    if '$ref' in rule:
        prefix = '#/$defs/'
        _require(rule['$ref'].startswith(prefix), 'only local schema references supported')
        _validate(value, schema['$defs'][rule['$ref'][len(prefix):]], schema, location)
        # Reference siblings still constrain the same value; never skip them.
    if 'enum' in rule:
        _require(any(type(value) is type(candidate) and value == candidate
                     for candidate in rule['enum']), f'{location}: incompatible value/version; expected enum')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int,
             'boolean': bool, 'number': (int, float)}
    kind = rule.get('type')
    if kind:
        expected = types[kind]
        valid = type(value) in expected if isinstance(expected, tuple) else type(value) is expected
        _require(valid, f'{location}: expected {kind}')
    if type(value) in (int, float):
        _require(type(value) is int or math.isfinite(value), f'{location}: number must be finite')
        if 'minimum' in rule:
            _require(value >= rule['minimum'], f'{location}: below minimum')
    if kind == 'object':
        _require(set(rule.get('required', [])) <= value.keys(),
                 f'{location}: missing required fields {set(rule.get("required", [])) - value.keys()}')
        props = rule.get('properties', {})
        if rule.get('additionalProperties') is False:
            _require(value.keys() <= props.keys(), f'{location}: unknown additional fields {value.keys() - props.keys()}')
        for key, child in value.items():
            if key in props:
                _validate(child, props[key], schema, f'{location}.{key}')
    if kind == 'array':
        _require(len(value) >= rule.get('minItems', 0), f'{location}: too few items')
        _require(len(value) <= rule.get('maxItems', len(value)), f'{location}: too many items')
        if rule.get('uniqueItems'):
            serial = [json.dumps(v, sort_keys=True, allow_nan=False) for v in value]
            _require(len(set(serial)) == len(serial), f'{location}: duplicate array value')
        for i, child in enumerate(value):
            _validate(child, rule['items'], schema, f'{location}[{i}]')
    if kind == 'string':
        _require(len(value) >= rule.get('minLength', 0), f'{location}: empty string')
        if 'pattern' in rule:
            _require(re.search(rule['pattern'], value) is not None, f'{location}: invalid string pattern')


def _index(rows, key):
    result = {}
    for row in rows:
        name = row[key]
        _require(name not in result, f'duplicate {key}: {name}')
        result[name] = row
    return result


def _references(data):
    actors = _index(data['actors'], 'actor_id')
    artifacts = _index(data['artifacts'], 'artifact_id')
    profiles = _index(data['profiles'], 'profile_id')
    items = _index(data['knowledge_items'], 'item_id')
    sources = _index(data['sources'], 'source_id')
    parameters = _index(data['parameters'], 'parameter_id')
    decisions = _index(data['decisions'], 'decision_id')
    scopes = _index(data['decisions'], 'scope')
    grants = _index(data['grants'], 'grant_id')
    for collection, key in [('holdings', 'holding_id'), ('functions', 'function_id'),
                            ('policies', 'policy_id'), ('channels', 'channel_id'), ('worlds', 'world_id')]:
        _index(data[collection], key)

    for p in parameters.values():
        lo, hi = p['range']
        low, high = p['sensitivity_range']
        _require(lo <= p['value'] <= hi and lo <= low <= high <= hi,
                 f'{p["parameter_id"]}: value/sensitivity outside admissible range')
        if p['unit'] == 'probability':
            _require(0 <= lo <= hi <= 1, f'{p["parameter_id"]}: probability range must be within [0, 1]')
        else:
            _require(type(p['value']) is int and lo >= 0,
                     f'{p["parameter_id"]}: count/unit requires nonnegative integer')

    def parameter(name, unit, minimum=0):
        _require(name in parameters, f'unknown parameter reference: {name}')
        p = parameters[name]
        _require(p['unit'] == unit, f'{name}: invalid unit; expected {unit}')
        _require(p['value'] >= minimum, f'{name}: parameter below minimum {minimum}')
        return p['value']

    def actor(name):
        _require(name in actors, f'unknown actor/endpoint: {name}')

    parameter(data['goal']['target'], 'probability')
    parameter(data['goal']['observation_window'], 'ticks', 1)
    _require(set(data['work_item']['decision_ids']) == decisions.keys(), 'work item must reference all decisions')
    _require(sum(p['kind'] == 'agent' for p in profiles.values()) <= 3, 'at most three agent profiles')
    for p in profiles.values():
        preferences = _index(p['preferences'], 'decision_id')
        _require(preferences.keys() == decisions.keys(), 'profile preferences must cover all decisions')
        for name, pref in preferences.items():
            _require(set(pref['options']) == set(decisions[name]['alternatives']), 'preference must rank exactly possible options')
        parameter(p['work_ticks'], 'ticks', 1)
        parameter(p['work_cost'], 'resource_units')
        parameter(p['availability'], 'probability')
    for a in actors.values():
        _require(a['profile_id'] in profiles, 'unknown profile reference')
    for artifact in artifacts.values():
        for reader in artifact['reader_ids']:
            actor(reader)
    for holding in data['holdings']:
        owner = holding['holder']
        registry = actors if owner['kind'] == 'actor' else artifacts
        _require(owner['holder_id'] in registry, f'unknown holder: {owner["holder_id"]}')
        _require(holding['item_id'] in items, 'unknown knowledge item')
        _require(holding['item_version'] == items[holding['item_id']]['version'], 'unknown item version')
        _require(set(holding['source_ids']) <= sources.keys(), 'unknown source reference')
        _require(owner['kind'] != 'artifact' or holding['explicit'], 'artifact holding must be explicit')
    for function in data['functions']:
        for name in function['actor_ids']:
            actor(name)
    for d in decisions.values():
        _require(d['alternatives'], 'decision needs possible options')
        _require(set(d['source_item_ids']) <= items.keys(), 'unknown decision source item')
        semantics = _index(d['option_semantics'], 'option')
        _require(semantics.keys() == set(d['alternatives']), 'semantics must cover every possible option')
        for spec in semantics.values():
            _require(set(spec['parameter_ids']) <= parameters.keys(), 'unknown option parameter')
            expected = {'retry_count': 'attempts', 'backoff': 'ticks'}.get(d['decision_id'])
            if expected:
                for name in spec['parameter_ids']:
                    parameter(name, expected)
    for grant in grants.values():
        actor(grant['actor_id'])
        _require(grant['scope'] in scopes, 'unknown authority scope')
        _require(grant['options'] and set(grant['options']) <= set(scopes[grant['scope']]['alternatives']),
                 'authority options outside scope')
    for policy in data['policies']:
        _require(policy['decision_id'] in decisions, 'unknown policy decision')
        decision = decisions[policy['decision_id']]
        _require(policy['option'] in decision['alternatives'], 'impossible policy option')
        _require(policy['grant_id'] in grants, 'unknown authority grant')
        grant = grants[policy['grant_id']]
        _require(grant['actor_id'] == policy['actor_id'] and grant['scope'] == decision['scope']
                 and policy['option'] in grant['options'], 'unauthorized policy authority reference')
        _require(policy['knowledge_item_id'] in items, 'unknown policy knowledge item')
        item = items[policy['knowledge_item_id']]
        _require(item['topic'] == decision['topic'] and item['proposition'] == policy['option'],
                 'policy knowledge must describe the scoped belief option')
    units = {'latency': ('ticks', 1), 'capacity': ('messages_per_tick', 1),
             'loss_probability': ('probability', 0), 'distortion_probability': ('probability', 0),
             'transfer_cost': ('resource_units', 0), 'connection_cost': ('resource_units', 0),
             'trust': ('probability', 0)}
    for channel in data['channels']:
        actor(channel['sender'])
        actor(channel['recipient'])
        _require(channel['sender'] != channel['recipient'], 'channel needs distinct endpoints')
        for key, (unit, minimum) in units.items():
            value = parameter(channel[key], unit, minimum)
            if key == 'distortion_probability':
                _require(value == 0, 'v1 scenario has no authored distortion rule; probability must be zero')
    for world in data['worlds']:
        mix = [parameter(name, 'probability') for name in world['mix'].values()]
        _require(math.isclose(sum(mix), 1, rel_tol=0, abs_tol=1e-9), 'world failure mix probabilities must sum to one')
        for name in world['recovery'].values():
            parameter(name, 'probability')
        for key, unit in [('duplicate_probability', 'probability'), ('retry_cost', 'resource_units'),
                          ('abandonment_probability', 'probability'), ('observation_lag', 'ticks'),
                          ('workload_rate', 'payments_per_tick')]:
            parameter(world[key], unit)


class Scenario:
    """Validated trusted initial inputs; snapshots describe initial access only.

    Future runtime services must query their live KnowledgeStore after commands.
    Do not give an actor this owner or audit_data; give it the detached projection.
    """
    def __init__(self, data, sha256):
        self._data = deepcopy(data)
        self.sha256 = sha256
        self._actors = _index(self._data['actors'], 'actor_id')
        self._profiles = _index(self._data['profiles'], 'profile_id')
        self._decisions = _index(self._data['decisions'], 'decision_id')
        self._initial_store = self.instantiate_knowledge(EventHistory('paymentco-initial'))

    def audit_data(self):
        """Detached private input for trusted engine setup and evidence review."""
        return deepcopy(self._data)

    def instantiate_knowledge(self, history):
        """Build a fresh simulation owner with explicit setup holdings at tick 0."""
        data = self._data
        store = KnowledgeStore(history,
            [Actor(a['actor_id'], a['kind'], a['team_id']) for a in data['actors']],
            [Artifact(a['artifact_id'], tuple(a['reader_ids'])) for a in data['artifacts']])
        for i in data['knowledge_items']:
            store.register_item(KnowledgeItem(**i))
        for h in data['holdings']:
            holding = KnowledgeHolding(
                holding_id=h['holding_id'], item=EntityRef('knowledge_item', h['item_id'], h['item_version']),
                holder=HolderRef(**h['holder']), source_ids=tuple(h['source_ids']),
                confidence=h['confidence'], freshness=h['freshness'], explicit=h['explicit'], accessible=h['accessible'])
            store.record_holding(holding, tick=0, command_id='setup.' + h['holding_id'], correlation_id='scenario.setup')
        return store

    def knowledge_for(self, actor_id):
        _require(actor_id in self._actors, 'unknown actor')
        return self._initial_store.view_for(actor_id)

    def question_for(self, decision_id):
        _require(decision_id in self._decisions, 'unknown decision')
        d = self._decisions[decision_id]
        return DecisionQuestion(d['decision_id'], d['topic'], d['scope'], tuple(d['alternatives']))

    def profile_for(self, actor_id, decision_id):
        _require(actor_id in self._actors, 'unknown actor')
        self.question_for(decision_id)
        profile = self._profiles[self._actors[actor_id]['profile_id']]
        pref = next(p for p in profile['preferences'] if p['decision_id'] == decision_id)
        return CapabilityProfile(tuple(pref['options']), profile['can_infer'], profile['read_claims'], profile['confidence'])

    def snapshot_for(self, actor_id):
        view = self.knowledge_for(actor_id)
        data = self._data
        return deepcopy(dict(
            scenario_id=data['scenario_id'], scenario_version=data['scenario_version'], actor_id=actor_id,
            goal=data['goal'], work_item=data['work_item'],
            goal_parameters={p['parameter_id']: p for p in data['parameters']
                             if p['parameter_id'] in (data['goal']['target'], data['goal']['observation_window'])},
            roster=[{k: a[k] for k in ('actor_id', 'name', 'kind', 'team_id', 'role')} for a in data['actors']],
            decisions=[{k: d[k] for k in ('decision_id', 'question', 'alternatives')} for d in data['decisions']],
            knowledge=[{'item': asdict(entry.item), 'holding': entry.holding.as_dict()} for entry in view.entries]))


def load_scenario(path, *, expected_hash=None):
    """Read UTF-8 JSON bytes, check identity then schema and domain references.

    Hash is SHA-256 of exact file bytes, separate from the scenario version. Pin
    it in a run manifest; formatting changes intentionally change file identity.
    Bundled schema is a trusted repository artifact, not caller supplied data.
    """
    try:
        raw = Path(path).read_bytes()
        schema = _decode(SCHEMA_PATH.read_bytes())
    except OSError as exc:
        raise ScenarioError(f'cannot read scenario/schema: {exc}') from exc
    digest = hashlib.sha256(raw).hexdigest()
    _require(expected_hash is None or expected_hash == digest, 'scenario hash mismatch')
    data = _decode(raw)
    _validate(data, schema, schema)
    _references(data)
    return Scenario(data, digest)
