"""Predeclared paired payment experiment; verification never overwrites evidence."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.artifacts import FAILURE_CATEGORIES
from agent_empires.simulation.events import canonical_json
from agent_empires.simulation.outcomes import MODEL_VERSION, PaymentInput, PaymentOutcomes, WorldRules, generate_workload
from agent_empires.simulation.randomness import RNG_SCHEME

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'research/experiments/AE-010/protocol.json'
INPUT = ROOT / 'scenarios/paymentco/scenario.json'
CANONICAL_FILES = ('runs.json', 'causal-traces.json')


def json_data(value):
    return json.loads(json.dumps(value, allow_nan=False))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def world_from_data(data, world_id, recovery_delay):
    parameters = {p['parameter_id']: p['value'] for p in data['parameters']}
    authored = next(w for w in data['worlds'] if w['world_id'] == world_id)
    return WorldRules(world_id,
                      tuple(parameters[authored['mix'][k]] for k in FAILURE_CATEGORIES),
                      tuple(parameters[authored['recovery'][k]] for k in FAILURE_CATEGORIES),
                      *(parameters[authored[k]] for k in ('duplicate_probability', 'retry_cost',
                          'abandonment_probability', 'observation_lag', 'workload_rate')),
                      recovery_delay)


def choices_for(strategy):
    choices = dict(retryable_types='all_failures', retry_count='three', backoff='fixed',
                   idempotency='stable_key', declined_handling='retry_all', audit_requirement='attempt_lineage')
    if strategy == 'no_retry':
        choices['retry_count'] = 'none'
    elif strategy == 'declines_blocked':
        choices['declined_handling'] = 'do_not_retry'
    elif strategy in ('soft_fixed', 'immediate'):
        choices['declined_handling'] = 'soft_only'
        if strategy == 'immediate':
            choices['backoff'] = 'immediate'
    elif strategy == 'unsafe_fixed':
        choices['idempotency'] = 'new_key'
    elif strategy != 'safe_fixed':
        raise ValueError('unknown predeclared strategy')
    return choices


def run_case(data, rules, workload, *, strategy, kind='agent', retain_history=False):
    variant = json_data(data)
    next(a for a in variant['actors'] if a['actor_id'] == 'jin').update(kind=kind, profile_id='implementer')
    raw = (json.dumps(variant, indent=2) + '\n').encode()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'scenario.json'
        path.write_bytes(raw)
        service = DeliveryService(load_scenario(path), run_id='ae010-payment')
    choices = choices_for(strategy)
    commands = []
    for name, option in choices.items():
        commands.append(dict(op='select', decision_id=name, option=option, actor_id='jin',
                             command_id='choose.' + name, expected_version=0, tick=0,
                             missing_information=['unvalidated-world:' + name]))
        service.decisions.select(name, option, actor_id='jin', expected_version=0, tick=0,
                                 command_id='choose.' + name, correlation_id='payment',
                                 reason='predeclared experiment strategy',
                                 missing_information=('unvalidated-world:' + name,))
    commands.extend([dict(op='start', actor_id='jin', command_id='work'), dict(op='step_delivery'),
                     dict(op='ship', command_id='ship', workload_hash=hashlib.sha256(canonical_json(json_data([asdict(p) for p in workload]))).hexdigest()),
                     dict(op='step_outcomes_until_idle')])
    service.start('jin', command_id='work')
    verification = service.step()
    engine = PaymentOutcomes(rules, service.history, service.clock)
    deployment = engine.ship(verification.proposal, workload, command_id='ship')
    while engine.step() is not None:
        pass
    events = service.history.canonical_bytes()
    result = dict(strategy=strategy, actor_kind=kind, scenario_variant_sha256=hashlib.sha256(raw).hexdigest(),
                  world_rules=asdict(rules), ordered_commands=commands, shipped_tick=deployment.shipped_tick,
                  implementation=asdict(verification.proposal.behavior),
                  decision_refs=[d.ref.as_dict() for d in verification.proposal.decisions],
                  unsupported_refs=[r.as_dict() for r in verification.proposal.unsupported_decisions],
                  assurance={a.dimension: a.status for a in verification.assessments},
                  goal=asdict(service.goal), metrics=engine.metrics(), results=[asdict(r) for r in engine.results],
                  history_sha256=hashlib.sha256(events).hexdigest())
    trace = json.loads(events) if retain_history else None
    return json_data(result), trace


def physical_results(results):
    """Observation interleaving changes event sequence IDs, not payment fields."""
    return [{k: v for k, v in result.items() if k != 'event_id'} for result in results]


def collect(protocol):
    data = json.loads(INPUT.read_bytes())
    parameters = {p['parameter_id']: p['value'] for p in protocol['parameters']}
    runs, traces, workloads = {}, {}, {}
    controls = {}
    for world_id in protocol['worlds']:
        rules = world_from_data(data, world_id, parameters['outcomes.recovery_delay'])
        for seed in protocol['seeds']:
            prefix = f'{world_id}/seed-{seed}'
            workload = generate_workload(rules, seed=seed, arrival_window=parameters['experiment.arrival_window'])
            workloads[prefix] = json_data([asdict(p) for p in workload])
            for strategy in protocol['strategies']:
                key = prefix + '/' + strategy
                runs[key], trace = run_case(data, rules, workload, strategy=strategy, retain_history=seed == 0)
                if trace:
                    traces[key] = trace
            for control in protocol['controls']:
                control_rules, control_workload, kind = rules, workload, 'agent'
                if control == 'matched_human':
                    kind = 'human'
                elif control == 'no_traffic':
                    control_workload = ()
                elif control == 'zero_duplicate_exposure':
                    control_rules = replace(rules, duplicate_probability=0)
                elif control == 'zero_recovery':
                    control_rules = replace(rules, recovery=(0, 0, 0, 0), duplicate_probability=0)
                elif control == 'fast_monitoring':
                    control_rules = replace(rules, observation_lag=0)
                else:
                    raise ValueError('unknown protocol control')
                key = prefix + '/' + control
                runs[key], trace = run_case(data, control_rules, control_workload, strategy='unsafe_fixed',
                                            kind=kind, retain_history=seed == 0)
                if trace:
                    traces[key] = trace
            baseline = runs[prefix + '/unsafe_fixed']
            controls[prefix] = dict(
                matched_kind_history_equal=baseline['history_sha256'] == runs[prefix + '/matched_human']['history_sha256'],
                monitoring_preserves_results=(physical_results(baseline['results']) == physical_results(runs[prefix + '/fast_monitoring']['results'])
                    and baseline['metrics'] == runs[prefix + '/fast_monitoring']['metrics']),
                no_traffic_no_incident=runs[prefix + '/no_traffic']['metrics']['duplicate_charges'] == 0,
                no_traffic_goal_rate_unknown=runs[prefix + '/no_traffic']['metrics']['abandonment_rate'] is None,
                no_duplicate_exposure_no_incident=runs[prefix + '/zero_duplicate_exposure']['metrics']['duplicate_charges'] == 0,
                no_recovery_no_recovered=runs[prefix + '/zero_recovery']['metrics']['recovered'] == 0,
                stable_key_no_duplicates=runs[prefix + '/safe_fixed']['metrics']['duplicate_charges'] == 0,
                all_feedback_delivered=all(runs[prefix + '/' + name]['metrics']['pending'] == 0
                    and runs[prefix + '/' + name]['metrics']['observed_count'] == runs[prefix + '/' + name]['metrics']['eligible']
                    for name in protocol['strategies'] + protocol['controls']),
            )
    # Explicit boundaries supplement random draws, rather than replacing incident-free seeds.
    boundary_world = WorldRules('boundary', (1, 0, 0, 0), (1, 1, 0, 1), 1, 1, 1, 5, 1, 1)
    boundaries = {
        'favorable': ('safe_fixed', PaymentInput('p', 0, 'transient', 0, (0, 0, 0), (0, 0, 0, 0))),
        'unfavorable': ('safe_fixed', PaymentInput('p', 0, 'hard_decline', 0, (0, 0, 0), (0, 0, 0, 0))),
        'harmful_human': ('unsafe_fixed', PaymentInput('p', 0, 'ambiguous', 0, (0, 0, 0), (0, 0, 0, 0))),
        'successful_agent': ('safe_fixed', PaymentInput('p', 0, 'ambiguous', 0, (0, 0, 0), (0, 0, 0, 0))),
        'harmless_unsupported': ('unsafe_fixed', PaymentInput('p', 0, 'transient', 0, (0, 0, 0), (0, 0, 0, 0))),
    }
    for name, (strategy, sample) in boundaries.items():
        key = 'boundary/' + name
        runs[key], traces[key] = run_case(data, boundary_world, (sample,), strategy=strategy,
                                         kind='human' if name == 'harmful_human' else 'agent', retain_history=True)
    controls['boundaries'] = dict(
        favorable_recovers=runs['boundary/favorable']['metrics']['recovered'] == 1,
        unfavorable_abandons=runs['boundary/unfavorable']['metrics']['abandoned'] == 1,
        identical_behavior_different_outcome=runs['boundary/favorable']['implementation'] == runs['boundary/unfavorable']['implementation'],
        human_can_harm=runs['boundary/harmful_human']['metrics']['duplicate_charges'] == 1,
        agent_can_succeed=runs['boundary/successful_agent']['metrics']['completed'] == 1 and runs['boundary/successful_agent']['metrics']['duplicate_charges'] == 0,
        unsupported_can_be_harmless=bool(runs['boundary/harmless_unsupported']['unsupported_refs']) and runs['boundary/harmless_unsupported']['metrics']['duplicate_charges'] == 0,
    )
    failed = [prefix + '/' + name for prefix, values in controls.items() for name, passed in values.items() if not passed]
    analysis = {}
    for world_id in protocol['worlds']:
        paired = []
        for seed in protocol['seeds']:
            base = f'{world_id}/seed-{seed}/'
            blocked, soft = runs[base + 'declines_blocked']['metrics'], runs[base + 'soft_fixed']['metrics']
            safe, unsafe = runs[base + 'safe_fixed']['metrics'], runs[base + 'unsafe_fixed']['metrics']
            paired.append(dict(seed=seed, soft_minus_blocked_abandoned=soft['abandoned'] - blocked['abandoned'],
                               soft_minus_blocked_cost=soft['retry_cost'] - blocked['retry_cost'],
                               unsafe_minus_safe_duplicates=unsafe['duplicate_charges'] - safe['duplicate_charges']))
        distributions = {}
        for strategy in protocol['strategies']:
            values = [runs[f'{world_id}/seed-{seed}/{strategy}']['metrics'] for seed in protocol['seeds']]
            distributions[strategy] = {metric: dict(mean=statistics.mean(v[metric] for v in values),
                min=min(v[metric] for v in values), max=max(v[metric] for v in values))
                for metric in ('abandoned', 'completed', 'duplicate_charges', 'retry_cost', 'terminal_latency_ticks')}
        analysis[world_id] = dict(paired_differences=paired, distributions=distributions,
            soft_policy_better_seeds=[p['seed'] for p in paired if p['soft_minus_blocked_abandoned'] < 0],
            soft_policy_worse_seeds=[p['seed'] for p in paired if p['soft_minus_blocked_abandoned'] > 0],
            soft_policy_equal_seeds=[p['seed'] for p in paired if p['soft_minus_blocked_abandoned'] == 0],
            unsafe_incident_free_seeds=[seed for seed in protocol['seeds'] if runs[f'{world_id}/seed-{seed}/unsafe_fixed']['metrics']['duplicate_charges'] == 0])
    inputs = ['scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
              'src/agent_empires/application/scenarios.py', 'src/agent_empires/application/services.py',
              'experiments/paymentco_slice.py', 'research/experiments/AE-010/protocol.json']
    inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/agent_empires/simulation').glob('*.py'))]
    manifest = dict(model_version=MODEL_VERSION, scenario_version=data['scenario_version'], rng_scheme=RNG_SCHEME,
                    python=platform.python_version(), input_sha256={p: sha(ROOT / p) for p in inputs},
                    protocol=protocol, parameter_provenance=data['parameters'] + protocol['parameters'],
                    workloads=workloads, runs=runs, controls=controls, failed_controls=failed, analysis=analysis,
                    negative_findings=[
                        'Immediate retries exhaust before the readiness threshold unless they acknowledge a hidden stable-key execution.',
                        'Green conformance and unsupported choices appear in successful, failed and incident runs.',
                        'World A soft-decline retries can spend resources without recovering or improving abandonment; all per-seed ties/reversals remain in analysis.',
                        'Unsafe new-key behavior can be incident-free when hidden execution or subsequent success is absent.',
                        'The invented 0.1 goal target need not be met by any strategy; fitness is not auto-promoted from these results.'
                    ], limitations=protocol['limits'])
    return json_data(manifest), dict(model_version=MODEL_VERSION, traces=traces)


def author(directory, protocol):
    directory.mkdir(parents=True, exist_ok=True)
    for name in (*CANONICAL_FILES, 'timing.json'):
        if (directory / name).exists():
            raise FileExistsError(f'refusing to overwrite evidence: {directory / name}')
    saved_protocol = directory / 'protocol.json'
    if saved_protocol.exists():
        if saved_protocol.read_bytes() != PROTOCOL.read_bytes():
            raise ValueError('saved protocol differs')
    else:
        saved_protocol.write_bytes(PROTOCOL.read_bytes())
    start = time.perf_counter()
    runs, traces = collect(protocol)
    for name, value in zip(CANONICAL_FILES, (runs, traces), strict=True):
        with (directory / name).open('x') as output:
            json.dump(value, output, indent=2, allow_nan=False)
            output.write('\n')
    elapsed = time.perf_counter() - start
    budget = next(p['value'] for p in protocol['parameters'] if p['parameter_id'] == 'experiment.wall_budget')
    timing = dict(elapsed_seconds=elapsed, budget_seconds=budget, passed=elapsed <= budget)
    (directory / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    if runs['failed_controls']:
        raise RuntimeError(f"failed controls retained: {runs['failed_controls']}")
    if not timing['passed']:
        raise RuntimeError(f'fresh run exceeds declared budget: {timing}')
    return timing


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    if platform.python_version() != '3.12.13':
        raise RuntimeError('experiment requires selected CPython 3.12.13')
    protocol = json.loads(PROTOCOL.read_bytes())
    if args.verify_against:
        if (args.verify_against / 'protocol.json').read_bytes() != PROTOCOL.read_bytes():
            raise ValueError('reviewed protocol differs')
        with tempfile.TemporaryDirectory() as directory:
            timing = author(Path(directory), protocol)
            for name in CANONICAL_FILES:
                fresh = json.loads((Path(directory) / name).read_bytes())
                saved = json.loads((args.verify_against / name).read_bytes())
                if canonical_json(fresh) != canonical_json(saved):
                    raise ValueError(f'canonical evidence differs: {name}')
        print(f"PASS: canonical runs/traces reproduced without overwriting; fresh timing {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s")
    else:
        timing = author(args.output_dir, protocol)
        print(f"PASS: authored all seeds/controls; timing {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s")
    return 0


if __name__ == '__main__':
    sys.exit(main())
