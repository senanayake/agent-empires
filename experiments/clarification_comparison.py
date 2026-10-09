"""Held-fixed clarification comparison; reviewed evidence is never overwritten."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.artifacts import FAILURE_CATEGORIES
from agent_empires.simulation.communication import Channel
from agent_empires.simulation.decisions import CapabilityProfile
from agent_empires.simulation.events import canonical_json
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem
from agent_empires.simulation.learning import Clarification, MODEL_VERSION
from agent_empires.simulation.outcomes import PaymentOutcomes, WorldRules, generate_workload
from agent_empires.simulation.randomness import NamedRandomness, RNG_SCHEME

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'research/experiments/AE-012'
INPUT = ROOT / 'scenarios/paymentco/scenario.json'


def json_data(value):
    return json.loads(json.dumps(value, allow_nan=False))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def load_inputs():
    return json.loads(INPUT.read_bytes()), json.loads((EVIDENCE / 'protocol.json').read_bytes())


def world_from_data(data, world_id, recovery_delay):
    params = {p['parameter_id']: p['value'] for p in data['parameters']}
    authored = next(w for w in data['worlds'] if w['world_id'] == world_id)
    return WorldRules(world_id, tuple(params[authored['mix'][k]] for k in FAILURE_CATEGORIES),
                      tuple(params[authored['recovery'][k]] for k in FAILURE_CATEGORIES),
                      *(params[authored[k]] for k in ('duplicate_probability', 'retry_cost',
                        'abandonment_probability', 'observation_lag', 'workload_rate')), recovery_delay)


def run_arm(data, protocol, rules, workload, condition, timing, *, seed, clarify, kind='agent'):
    variant = json_data(data)
    next(a for a in variant['actors'] if a['actor_id'] == 'jin').update(kind=kind, profile_id='implementer')
    raw = (json.dumps(variant, indent=2) + '\n').encode()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'scenario.json'
        path.write_bytes(raw)
        service = DeliveryService(load_scenario(path), run_id='ae012-paired')
    commands = []
    # Authored wrong/stale holdings change Ada's live access in BOTH arms.
    if condition in ('wrong', 'stale'):
        service.knowledge.set_holding_access('interface_rationale.ada', False, tick=0,
                                            command_id='setup.hide', correlation_id='setup')
        commands.append({'op': 'hide', 'holding': 'interface_rationale.ada'})
    if condition in ('wrong', 'stale', 'conflicting'):
        item = KnowledgeItem('ae012.answer', 1, 'idempotency',
                             'stable_key' if condition == 'stale' else 'new_key')
        holding = KnowledgeHolding('ae012.answer.ada', item.ref, HolderRef('actor', 'ada'),
                                   ('interface_rationale.source',), 'high',
                                   'stale' if condition == 'stale' else 'current', True)
        service.knowledge.register_item(item)
        service.knowledge.record_holding(holding, tick=0, command_id='setup.answer', correlation_id='setup')
        commands.append({'op': 'record_answer_holding', 'item': asdict(item), 'holding': asdict(holding)})
    preference = ('stable_key', 'new_key', 'unspecified') if condition == 'wrong' else ('new_key', 'stable_key', 'unspecified')
    profile = CapabilityProfile(preference, confidence='high')
    commands.append({'op': 'infer', 'profile': asdict(profile), 'expected_version': 0, 'tick': 0})
    decision = service.decisions.infer('idempotency', 'jin', profile, expected_version=0, tick=0,
                                      command_id='infer', correlation_id='story',
                                      missing_information=('interface rationale missing',))
    answer_result, channel_cost = None, 0
    if clarify:
        owner = Clarification(service.knowledge, service.authority, service.clock, service.history, NamedRandomness(seed))
        request = Channel('ask', 'jin', 'ada', timing['latency'], protocol['channel_capacity'],
                          transfer_cost=protocol['request_cost'])
        response = Channel('answer', 'ada', 'jin', timing['latency'], protocol['channel_capacity'],
                           loss_probability=protocol['lossy_probability'] if condition == 'lossy' else 0,
                           transfer_cost=protocol['answer_cost'])
        owner.connect(request)
        owner.connect(response)
        availability = None if condition == 'unavailable' else timing['available_at']
        grant_id = 'grant.audit_requirement' if condition == 'out_of_scope' else 'grant.idempotency'
        commands.append({'op': 'clarify', 'request': asdict(request), 'response': asdict(response),
                         'available_at': availability, 'service_ticks': protocol['service_ticks'],
                         'timeout': protocol['timeout_ticks'], 'grant_id': grant_id})
        owner.ask(service.scenario.question_for('idempotency'), requester='jin', holder='ada',
                  request_channel='ask', answer_channel='answer', command_id='query',
                  timeout=protocol['timeout_ticks'], available_at=availability,
                  service_ticks=protocol['service_ticks'], grant_id=grant_id)
        while (work := service.clock.pop_next()) is not None:
            owner.dispatch(work)
        answer_result = asdict(owner.result('query'))
        decision = owner.select('query', service.decisions, profile, expected_version=1, command_id='choose.idempotency')
        channel_cost = owner.total_cost
        commands.append({'op': 'select_after_clarification', 'expected_version': 1, 'tick': service.clock.now})
    fixed_choices = dict(retryable_types='all_failures', retry_count='three', backoff='fixed',
                         declined_handling='retry_all', audit_requirement='attempt_lineage')
    for name, option in fixed_choices.items():
        commands.append({'op': 'select', 'decision_id': name, 'option': option, 'tick': service.clock.now})
        service.decisions.select(name, option, actor_id='jin', expected_version=0, tick=service.clock.now,
                                 command_id='choose.' + name, correlation_id='story',
                                 reason='held-fixed workload comparison', missing_information=('unvalidated:' + name,))
    service.start('jin', command_id='work')
    verification = service.step()
    engine = PaymentOutcomes(rules, service.history, service.clock)
    deployment = engine.ship(verification.proposal, workload, command_id='ship')
    while engine.step() is not None:
        pass
    commands.extend([{'op': 'start', 'actor': 'jin', 'command_id': 'work'},
                     {'op': 'step_delivery'}, {'op': 'ship', 'command_id': 'ship'}, {'op': 'drain_outcomes'}])
    trace = json.loads(service.history.canonical_bytes())
    result = dict(selected=decision.selected, authority_basis=decision.authority_basis, support=decision.support,
                  backed_source_ids=list(decision.backed_source_ids), decision_version=decision.version,
                  decision_sources=list(decision.source_ids), clarification=answer_result,
                  channel_cost=channel_cost, work_cost=service.spent_resource_units,
                  ship_tick=deployment.shipped_tick, final_observation_tick=service.clock.now,
                  workload_sha256=sha(canonical_json(json_data([asdict(p) for p in workload]))),
                  scenario_variant_sha256=sha(raw), ordered_commands=json_data(commands),
                  world_rules=json_data(asdict(rules)), metrics=engine.metrics(),
                  assurance={a.dimension: a.status for a in verification.assessments},
                  history_sha256=sha(service.history.canonical_bytes()))
    return json_data(result), trace


def paired_case(data, protocol, world_id, seed, condition, timing):
    rules = world_from_data(data, world_id, protocol['recovery_delay'])
    workload = generate_workload(rules, seed=seed, arrival_window=protocol['arrival_window'])
    if condition == 'harmless':
        rules = replace(rules, duplicate_probability=0)
    baseline, before = run_arm(data, protocol, rules, workload, condition, timing, seed=seed, clarify=False)
    asked, after = run_arm(data, protocol, rules, workload, condition, timing, seed=seed, clarify=True)
    differences = {metric: asked['metrics'][metric] - baseline['metrics'][metric]
                   for metric in ('duplicate_charges', 'abandoned', 'completed', 'retry_cost')}
    differences.update(ship_ticks=asked['ship_tick'] - baseline['ship_tick'],
                       channel_cost=asked['channel_cost'] - baseline['channel_cost'],
                       work_cost=asked['work_cost'] - baseline['work_cost'])
    cost_grid = {f'duplicate={penalty}/delay={delay}':
                 differences['duplicate_charges'] * penalty + differences['retry_cost']
                 + differences['work_cost'] + differences['channel_cost'] + differences['ship_ticks'] * delay
                 for penalty in protocol['duplicate_penalties'] for delay in protocol['delay_costs_per_tick']}
    controls = dict(workload_equal=baseline['workload_sha256'] == asked['workload_sha256'],
                    scenario_equal=baseline['scenario_variant_sha256'] == asked['scenario_variant_sha256'],
                    world_equal=baseline['world_rules'] == asked['world_rules'],
                    no_implicit_authority=asked['authority_basis'] == 'inferred_without_authority',
                    no_independent_support=asked['backed_source_ids'] == [],
                    all_payments_finished=baseline['metrics']['pending'] == asked['metrics']['pending'] == 0,
                    green_implementation=all(arm['assurance']['implementation_conformance'] == 'pass'
                                             for arm in (baseline, asked)))
    if condition == 'stale':
        controls['stale_no_change'] = baseline['selected'] == asked['selected']
    if condition == 'harmless':
        controls['no_duplicate_exposure'] = baseline['metrics']['duplicate_charges'] == asked['metrics']['duplicate_charges'] == 0
        controls['waiting_costly'] = all(cost_grid[f'duplicate={p}/delay={d}'] > 0
                                        for p in protocol['duplicate_penalties'] for d in protocol['delay_costs_per_tick'] if d > 0)
    pair = dict(world_id=world_id, seed=seed, condition=condition, timing=timing, inference=baseline,
                clarification=asked, differences=differences, cost_grid=cost_grid, controls=controls)
    if seed == 0:
        pair['_traces'] = {'inference': before, 'clarification': after}
    return pair


def collect(protocol):
    data = json.loads(INPUT.read_bytes())
    pairs, traces, workloads, failures, matched = {}, {}, {}, [], {}
    for world in protocol['worlds']:
        for seed in protocol['seeds']:
            rules = world_from_data(data, world, protocol['recovery_delay'])
            workload = generate_workload(rules, seed=seed, arrival_window=protocol['arrival_window'])
            workloads[f'{world}/seed-{seed}'] = json_data([asdict(p) for p in workload])
            for condition in protocol['conditions']:
                for timing in protocol['timing_profiles']:
                    key = f"{world}/seed-{seed}/{condition}/{timing['name']}"
                    pair = paired_case(data, protocol, world, seed, condition, timing)
                    if '_traces' in pair:
                        traces[key] = pair.pop('_traces')
                    failures.extend(key + '/' + name for name, value in pair['controls'].items() if not value)
                    pairs[key] = pair
        # Match kind on both arms, using the same capabilities and root seed.
        for clarify in (False, True):
            timing = protocol['timing_profiles'][0]
            rules = world_from_data(data, world, protocol['recovery_delay'])
            workload = generate_workload(rules, seed=protocol['seeds'][0], arrival_window=protocol['arrival_window'])
            agent, _ = run_arm(data, protocol, rules, workload, 'helpful', timing, seed=protocol['seeds'][0], clarify=clarify)
            human, _ = run_arm(data, protocol, rules, workload, 'helpful', timing, seed=protocol['seeds'][0], clarify=clarify, kind='human')
            key = f'{world}/clarify-{clarify}'
            matched[key] = agent['history_sha256'] == human['history_sha256']
            if not matched[key]:
                failures.append(key + '/kind-history')
    analysis = {}
    for world in protocol['worlds']:
        for condition in protocol['conditions']:
            for timing in protocol['timing_profiles']:
                group = [pairs[f"{world}/seed-{seed}/{condition}/{timing['name']}"] for seed in protocol['seeds']]
                distributions = {metric: dict(mean=statistics.mean(p['differences'][metric] for p in group),
                                             min=min(p['differences'][metric] for p in group),
                                             max=max(p['differences'][metric] for p in group),
                                             population_sd=statistics.pstdev(p['differences'][metric] for p in group))
                                 for metric in group[0]['differences']}
                grid = {cell: dict(mean=statistics.mean(p['cost_grid'][cell] for p in group),
                                   min=min(p['cost_grid'][cell] for p in group),
                                   max=max(p['cost_grid'][cell] for p in group),
                                   better_seeds=[p['seed'] for p in group if p['cost_grid'][cell] < 0],
                                   tied_seeds=[p['seed'] for p in group if p['cost_grid'][cell] == 0],
                                   worse_seeds=[p['seed'] for p in group if p['cost_grid'][cell] > 0])
                        for cell in group[0]['cost_grid']}
                analysis[f"{world}/{condition}/{timing['name']}"] = dict(
                    paired_differences=distributions, cost_grid=grid,
                    inference_incident_free_seeds=[p['seed'] for p in group if p['inference']['metrics']['duplicate_charges'] == 0],
                    answer_statuses={str(p['seed']): p['clarification']['clarification']['status'] for p in group})
    paths = ['scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
             'src/agent_empires/application/scenarios.py', 'src/agent_empires/application/services.py',
             'experiments/clarification_comparison.py', 'research/experiments/AE-012/protocol.md']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/agent_empires/simulation').glob('*.py'))]
    result = dict(model_version=MODEL_VERSION, python=platform.python_version(), rng_scheme=RNG_SCHEME,
                  protocol=protocol, input_sha256={p: sha((ROOT / p).read_bytes()) for p in paths},
                  parameter_provenance=data['parameters'], workloads=workloads, pairs=pairs,
                  matched_kind_controls=matched, failed_controls=failures, analysis=analysis, limits=protocol['limits'])
    return json_data(result), traces


def author(directory, protocol):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('results.json', 'traces.json', 'timing.json'):
        if (directory / name).exists():
            raise FileExistsError(f'refusing to overwrite evidence: {directory / name}')
    saved_protocol = json.dumps(protocol, indent=2) + '\n'
    target = directory / 'protocol.json'
    if target.exists():
        if json.loads(target.read_bytes()) != protocol:
            raise ValueError('saved protocol differs')
    else:
        target.write_text(saved_protocol)
    markdown = directory / 'protocol.md'
    if markdown.exists():
        if markdown.read_bytes() != (EVIDENCE / 'protocol.md').read_bytes():
            raise ValueError('saved protocol text differs')
    else:
        markdown.write_bytes((EVIDENCE / 'protocol.md').read_bytes())
    start = time.perf_counter()
    result, traces = collect(protocol)
    for name, value in (('results.json', result), ('traces.json', traces)):
        with (directory / name).open('x') as output:
            json.dump(value, output, indent=2, allow_nan=False)
            output.write('\n')
    timing = dict(elapsed_seconds=time.perf_counter() - start, budget_seconds=protocol['wall_budget_seconds'])
    timing['passed'] = timing['elapsed_seconds'] <= timing['budget_seconds']
    (directory / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    if result['failed_controls']:
        raise RuntimeError(f"failed controls retained: {result['failed_controls']}")
    if not timing['passed']:
        raise RuntimeError(f'fresh run exceeds declared budget: {timing}')
    return timing


def verify(directory, protocol):
    directory = Path(directory)
    if json.loads((directory / 'protocol.json').read_bytes()) != protocol:
        raise ValueError('reviewed protocol differs')
    if (directory / 'protocol.md').read_bytes() != (EVIDENCE / 'protocol.md').read_bytes():
        raise ValueError('reviewed protocol text differs')
    with tempfile.TemporaryDirectory() as temporary:
        timing = author(Path(temporary), protocol)
        for name in ('results.json', 'traces.json'):
            if canonical_json(json.loads((directory / name).read_bytes())) != canonical_json(json.loads((Path(temporary) / name).read_bytes())):
                raise ValueError(f'canonical evidence differs: {name}')
    return timing


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    if platform.python_version() != '3.12.13':
        raise RuntimeError('experiment requires CPython 3.12.13')
    _, protocol = load_inputs()
    timing = verify(args.verify_against, protocol) if args.verify_against else author(args.output_dir, protocol)
    print(f"PASS: {'verified without overwriting' if args.verify_against else 'authored'} paired results/traces; fresh timing {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s")


if __name__ == '__main__':
    main()
