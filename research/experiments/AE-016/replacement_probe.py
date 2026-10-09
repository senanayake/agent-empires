"""Bounded public-API replacement traces; author once or verify without writes."""
import argparse
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import sys

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.actors import Actor
from agent_empires.simulation.communication import Channel
from agent_empires.simulation.events import EntityRef, canonical_json
from agent_empires.simulation.randomness import RNG_SCHEME

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = ROOT / 'scenarios/paymentco/scenario.json'
PROTOCOL = Path(__file__).with_name('protocol.json')
NEW = Actor('replacement', 'agent', 'engineering')
FUNCTIONS = ('domain_interpreter', 'historian', 'product_engineering_bridge')
SOURCE_PATHS = (
    'src/agent_empires/simulation/organization.py', 'src/agent_empires/simulation/knowledge.py',
    'src/agent_empires/simulation/communication.py', 'src/agent_empires/simulation/decisions.py',
    'src/agent_empires/application/services.py', 'src/agent_empires/application/scenarios.py',
    'src/agent_empires/simulation/actors.py', 'src/agent_empires/simulation/artifacts.py',
    'src/agent_empires/simulation/assurance.py', 'src/agent_empires/simulation/clock.py',
    'src/agent_empires/simulation/events.py', 'src/agent_empires/simulation/randomness.py',
    'research/experiments/AE-016/replacement_probe.py', 'research/experiments/AE-016/protocol.json',
    'scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
)


def engine(seed=0):
    return DeliveryService(load_scenario(SCENARIO), run_id='ae016-trace', root_seed=seed)


def holding(service, actor):
    return service.knowledge.view_for(actor).entries[0].holding.holding_id


def replace_actor(service, old='sarah', *, profile='implementer'):
    return service.replace_actor(old, NEW, profile_id=profile, role='senior engineer', command_id='replace')


def diagnostic(service):
    """Trusted experiment-only projection; never a player snapshot."""
    return {
        'tick': service.clock.now,
        'engineering_members': list(service.organization.members('engineering')),
        'function_holders': {f: list(service.organization.function_holders(f)) for f in FUNCTIONS},
        'uncovered_functions': list(service.organization.uncovered_functions),
        'historical_scope_available': service.knowledge.organization_available(
            EntityRef('knowledge_item', 'historical_scope', 1)),
        'channels': [asdict(c) for c in service.communication.channels],
        'work_cost': service.spent_resource_units, 'communication_cost': service.communication.total_cost,
        'pending_count': service.clock.pending_count,
        'proposals': [dict(actor=p.actor_id, behavior=asdict(p.behavior), completed_tick=p.completed_tick,
                           resource_cost=p.resource_cost, unsupported_decisions=[r.as_dict() for r in p.unsupported_decisions])
                      for p in service.proposals],
    }


def record(service, before, controls):
    return dict(before=before, after=diagnostic(service), controls=controls,
                history=json.loads(service.history.canonical_bytes()))


def collect():
    traces = {}
    service = engine()
    before = diagnostic(service)
    replace_actor(service)
    traces['unprepared'] = record(service, before, {
        'three_functions_uncovered': set(FUNCTIONS) <= set(service.organization.uncovered_functions),
        'new_actor_empty': not service.knowledge.view_for(NEW.actor_id).entries,
        'no_incident_without_exposure': not any(e.event_type == 'IncidentOccurred' for e in service.history.events),
    })

    service = engine()
    service.organization.assign_function('historian', 'jin', tick=0, command_id='redundant.function', correlation_id='prepare')
    service.communication.send('sarah.to.jin', holding(service, 'sarah'), command_id='transfer', correlation_id='prepare')
    service.step()
    before = diagnostic(service)
    replace_actor(service)
    traces['redundant'] = record(service, before, {
        'history_preserved': service.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1)),
        'surviving_function': service.organization.function_holders('historian') == ('jin',),
    })

    service = engine()
    service.authority.delegate('old.grant', 'grant.idempotency', 'ada', 'sarah', options=('stable_key',),
        tick=0, command_id='delegate.old', correlation_id='authority')
    old = service.decisions.select('idempotency', 'stable_key', actor_id='sarah', grant_id='old.grant',
        expected_version=0, tick=0, command_id='choose.old', correlation_id='authority', reason='delegated')
    before = diagnostic(service)
    replace_actor(service)
    service.authority.delegate('new.grant', 'grant.idempotency', 'ada', NEW.actor_id, options=('stable_key',),
        tick=0, command_id='delegate.new', correlation_id='authority')
    new = service.decisions.select('idempotency', 'stable_key', actor_id=NEW.actor_id, grant_id='new.grant',
        expected_version=1, tick=0, command_id='choose.new', correlation_id='authority', reason='delegated')
    traces['explicit_delegation'] = record(service, before, {
        'delegated_without_evidence': new.authority_basis == 'delegated_discretion' and new.support == 'none',
        'old_choice_preserved': service.decisions.version('idempotency', 1) == old,
        'old_grant_explicitly_revoked': any(e.event_type == 'AuthorityRevoked' and e.payload['grant_id'] == 'old.grant'
                                          for e in service.history.events),
    })

    service = engine()
    before = diagnostic(service)
    replace_actor(service)
    snapshot = service.history.canonical_bytes()
    try:
        service.communication.send('maya.to.sarah', holding(service, 'maya'), command_id='stale', correlation_id='bridge')
    except ValueError as error:
        rejection = str(error)
    else:
        raise AssertionError('retired bridge accepted a send')
    traces['removed_bridge'] = record(service, before, {
        'rejected_without_mutation': snapshot == service.history.canonical_bytes(),
        'retired_edges': not any('sarah' in (c.sender, c.recipient) for c in service.communication.channels),
    })
    traces['removed_bridge']['rejection'] = rejection

    service = engine()
    service.communication.send('sarah.to.jin', holding(service, 'sarah'), command_id='outgoing', correlation_id='inflight')
    service.communication.send('maya.to.sarah', holding(service, 'maya'), command_id='incoming', correlation_id='inflight')
    old_job = service.start('sarah', command_id='old.work')
    before = diagnostic(service)
    replace_actor(service)
    service.start(NEW.actor_id, command_id='new.work')
    while service.step() is not None:
        pass
    traces['inflight'] = record(service, before, {
        'only_new_work_completed': len(service.proposals) == 1 and service.proposals[0].actor_id == NEW.actor_id,
        'cancelled_cost_retained': service.spent_resource_units == old_job.resource_cost + 2,
        'outgoing_snapshot_survives': service.knowledge.view_for('jin').lookup('historical_scope', 1) is not None,
        'incoming_lost': any(e.event_type == 'InformationLost' and e.payload['reason'] == 'recipient_unavailable'
                             for e in service.history.events),
    })

    baseline, service = engine(), engine()
    service.register_actor(NEW, profile_id='human', role='engineer', command_id='register')
    service.communication.connect(Channel('handover', 'sarah', NEW.actor_id, 1, 1), command_id='connect', correlation_id='prepare')
    service.communication.send('handover', holding(service, 'sarah'), command_id='transfer', correlation_id='prepare')
    service.step()
    for function in FUNCTIONS:
        service.organization.assign_function(function, NEW.actor_id, tick=1, command_id='assign.' + function, correlation_id='prepare')
    service.authority.delegate('prepared.grant', 'grant.idempotency', 'ada', NEW.actor_id, options=('stable_key',),
        tick=1, command_id='delegate', correlation_id='prepare')
    edges = [c for c in service.communication.channels if 'sarah' in (c.sender, c.recipient) and c.channel_id != 'handover']
    before = diagnostic(service)
    replace_actor(service, profile='human')
    for edge in edges:
        service.communication.connect(replace(edge, channel_id='new.' + edge.channel_id,
            sender=NEW.actor_id if edge.sender == 'sarah' else edge.sender,
            recipient=NEW.actor_id if edge.recipient == 'sarah' else edge.recipient),
            command_id='reconnect.' + edge.channel_id, correlation_id='prepare')
    old_job = baseline.start('sarah', command_id='work')
    new_job = service.start(NEW.actor_id, command_id='work')
    old_result, new_result = baseline.step(), service.step()
    traces['prepared'] = record(service, before, {
        'coverage_preserved': service.organization.uncovered_functions == (),
        'scope_preserved': service.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1)),
        'behavior_equal': old_result.proposal.behavior == new_result.proposal.behavior,
        'matched_duration_cost': (old_job.completion_tick-old_job.started_tick, old_job.resource_cost) == (
            new_job.completion_tick-new_job.started_tick, new_job.resource_cost),
    })
    traces['prepared']['baseline'] = diagnostic(baseline)

    service = engine()
    before = diagnostic(service)
    replace_actor(service, old='jin')
    traces['noncritical'] = record(service, before, {
        'sarah_functions_preserved': all(service.organization.function_holders(f) == ('sarah',) for f in FUNCTIONS),
        'scope_preserved': service.knowledge.organization_available(EntityRef('knowledge_item', 'historical_scope', 1)),
    })

    pairs = []
    for seed in json.loads(PROTOCOL.read_bytes())['seeds']:
        services = [engine(seed), engine(seed)]
        for service in services:
            service.communication.connect(Channel('paired', 'sarah', 'jin', 2, 1, loss_probability=0.4),
                command_id='paired.connect', correlation_id='paired')
            service.communication.send('paired', holding(service, 'sarah'), command_id='paired.send', correlation_id='paired')
        replace_actor(services[1])
        for service in services:
            service.step()
        facts = [next(e for e in service.history.events if e.command_id == 'paired.send'
                      and e.event_type in ('KnowledgeTransferred', 'InformationLost')) for service in services]
        pairs.append(dict(seed=seed, baseline=facts[0].as_dict(), replacement=facts[1].as_dict(),
                          equal=facts[0].payload == facts[1].payload and facts[0].event_type == facts[1].event_type))
    assert all(all(trace['controls'].values()) for trace in traces.values())
    assert all(pair['equal'] for pair in pairs)
    return dict(model_version='replacement-lifecycle-v1', traces=traces, seeded_pairs=pairs,
                negative_findings={
                    'lost_paired_seeds': [p['seed'] for p in pairs if p['replacement']['event_type'] == 'InformationLost'],
                    'unprepared_functions': traces['unprepared']['after']['uncovered_functions'],
                    'no_incident_exposure': 'No workload shipped; no world-risk reduction claim.',
                    'prepared_limit': 'Matched behavior/coverage/access, with explicit preparation time and channel cost; authority still requires scoped selection and choices remain unsupported.',
                    'noncritical_limit': 'Noncritical only relative to Sarah functions; Jin holdings and incoming channels still depart.',
                })


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    assert sys.version_info[:3] == (3, 12, 13), 'selected runtime required'
    target = args.output_dir or args.verify_against
    result_path, manifest_path = target / 'replacement-traces.json', target / 'manifest.json'
    if args.output_dir and (result_path.exists() or manifest_path.exists()):
        parser.error('refusing to overwrite authored canonical evidence')
    result = canonical_json(collect()) + b'\n'
    manifest = canonical_json(dict(
        model_version='replacement-lifecycle-v1', python_version=sys.version.split()[0],
        rng_scheme=RNG_SCHEME,
        inputs={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCE_PATHS},
        result_sha256=sha256(result).hexdigest(),
    )) + b'\n'
    if args.verify_against:
        if result_path.read_bytes() != result or manifest_path.read_bytes() != manifest:
            raise SystemExit('FAIL: canonical trace or current source/runtime binding mismatch')
        print('PASS: 7 replacement traces and 16 paired seeds reproduce; evidence unchanged')
    else:
        target.mkdir(parents=True, exist_ok=True)
        result_path.write_bytes(result)
        manifest_path.write_bytes(manifest)
        print('PASS: authored 7 replacement traces and 16 paired seeds; negatives retained')


if __name__ == '__main__':
    main()
