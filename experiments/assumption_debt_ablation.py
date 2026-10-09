"""Diagnostic-only ablation: fixed world outcomes, explicit toy scales, exact replay."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile
import time

# Support direct CLI invocation and import by focused tests, without installation
# of experiments as an application package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paymentco_slice import choices_for, world_from_data
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.events import canonical_json
from agent_empires.simulation.metrics import (
    AssumptionExposure, assumption_components, assumption_debt, candidate_product,
)
from agent_empires.simulation.outcomes import PaymentInput, PaymentOutcomes, WorldRules, generate_workload
from agent_empires.simulation.randomness import RNG_SCHEME

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'research/experiments/AE-014'
MODEL = 'assumption-debt-ablation-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scores(c):
    product = candidate_product(c)
    return dict(product=product, reversible_product=candidate_product(c, adjust_reversibility=True),
                geometric_mean=product ** 0.25,
                arithmetic_mean=(c.impact + c.uncertainty + c.propagation + c.persistence) / 4,
                impact_uncertainty=c.impact * c.uncertainty)


def diagnostic(record, *, window=16, cap=1, now_tick=16):
    return assumption_components(record, now_tick=now_tick, age_window=window, propagation_limit=cap)


def run(data, rules, workload, strategy, record, *, enable_diagnostic=True):
    service = DeliveryService(load_scenario(ROOT / 'scenarios/paymentco/scenario.json'), run_id='ae014')
    commands = []
    for name, option in choices_for(strategy).items():
        command = dict(decision_id=name, option=option, actor_id='jin', expected_version=0,
                       tick=0, command_id='choose.' + name, correlation_id='ae014',
                       reason='predeclared diagnostic comparison', missing_information=('unvalidated-world:' + name,))
        service.decisions.select(**command)
        commands.append(dict(op='select', **command))
    service.start('jin', command_id='work')
    verified = service.step()
    service.clock.advance_to(16)  # Predeclared idle aging before any world exposure.
    engine = PaymentOutcomes(rules, service.history, service.clock)
    # Actual diagnostic intervention runs before exposure and after every step.
    # Compare entire authoritative history with an otherwise identical disabled run.
    before = service.history.canonical_bytes()
    if enable_diagnostic:
        diagnostic(record)
    unchanged = before == service.history.canonical_bytes()
    deployment = engine.ship(verified.proposal, workload, command_id='ship')
    while engine.step() is not None:
        before = service.history.canonical_bytes() if enable_diagnostic else None
        if enable_diagnostic:
            diagnostic(record, now_tick=service.clock.now)
            unchanged &= before == service.history.canonical_bytes()
    commands.extend([dict(op='start', actor_id='jin', command_id='work'), dict(op='step_delivery'), dict(op='advance_idle', tick=16),
        dict(op='ship', command_id='ship', workload_sha256=hashlib.sha256(canonical_json(json.loads(json.dumps([asdict(p) for p in workload])))).hexdigest()),
        dict(op='step_outcomes_until_idle')])
    return dict(world=asdict(rules), workload=[asdict(p) for p in workload], ordered_commands=commands,
                implementation=asdict(verified.proposal.behavior),
                unsupported_refs=[r.as_dict() for r in verified.proposal.unsupported_decisions],
                deployment=deployment.ref.as_dict(), metrics=engine.metrics(),
                history_sha256=hashlib.sha256(service.history.canonical_bytes()).hexdigest(),
                diagnostic_preserved_history=unchanged)


def record_for(name, **changes):
    values = dict(assumption_id=name, impact=1, uncertainty=1, propagated_to=('proposal@1',),
                  created_tick=0, reversibility=0, source_ids=('authored-world-gap',))
    values.update(changes)
    return AssumptionExposure(**values)


def annotated(data, rules, workload, strategy, record):
    base = run(data, rules, workload, strategy, record, enable_diagnostic=False)
    observed = run(data, rules, workload, strategy, record)
    if base != observed:
        raise AssertionError('diagnostic changed authoritative history or outcomes')
    c = diagnostic(record)
    return dict(**observed, assumption=asdict(record), components=asdict(c), scores=scores(c),
                harm=observed['metrics']['duplicate_charges'] > 0,
                ablations=dict(no_scalar=dict(metrics=observed['metrics'],
                    behavior=observed['implementation'], workload_sha256=observed['ordered_commands'][-2]['workload_sha256']),
                    component_vector=asdict(c), candidate_product=candidate_product(c)))


def boundary_cases():
    data = json.loads((ROOT / 'scenarios/paymentco/scenario.json').read_bytes())
    rules = WorldRules('authored-boundary', (0, 0, 0, 1), (1, 1, 0, 1), 1, 1, 0, 5, 1, 1)
    ambiguous = (PaymentInput('p', 0, 'ambiguous', 0, (0, 0, 0), (0.9,) * 4),)
    transient = (replace(ambiguous[0], category='transient'),)
    specs = dict(harmful=('unsafe_fixed', ambiguous, record_for('harmful')),
        no_traffic=('unsafe_fixed', (), record_for('no_traffic')),
        transient=('unsafe_fixed', transient, record_for('transient')),
        protected=('safe_fixed', ambiguous, record_for('protected')),
        reversible_low_impact=('unsafe_fixed', (), record_for('low', impact=0.05, reversibility=1)),
        newborn_harm=('unsafe_fixed', ambiguous, record_for('newborn', created_tick=16)),
        collision_impact=('unsafe_fixed', ambiguous, record_for('impact', impact=0.25)),
        collision_uncertainty=('unsafe_fixed', (), record_for('uncertainty', uncertainty=0.25)))
    return {name: annotated(data, rules, workload, strategy, record)
            for name, (strategy, workload, record) in specs.items()}


def ranking(values, labels):
    pairs = [(a, b) for a, harmed in zip(values, labels) if harmed
                     for b, other in zip(values, labels) if not other]
    return (sum(1 if a > b else 0.5 if a == b else 0 for a, b in pairs) / len(pairs)) if pairs else None


def confusion(alerts, labels):
    return dict(true_positive=sum(a and b for a, b in zip(alerts, labels)),
                false_positive=sum(a and not b for a, b in zip(alerts, labels)),
                true_negative=sum(not a and not b for a, b in zip(alerts, labels)),
                false_negative=sum(not a and b for a, b in zip(alerts, labels)))


def analyze(cases):
    rows = list(cases.values())
    labels = [r['harm'] for r in rows]
    analysis = dict(no_scalar=dict(pairwise_concordance=ranking([0] * len(rows), labels),
                     confusion=confusion([False] * len(rows), labels)),
        component_vector=dict(confusion=confusion([r['components']['impact'] >= 0.5
            and r['components']['uncertainty'] >= 0.5 and r['components']['propagation'] > 0
            and r['components']['persistence'] > 0 for r in rows], labels)))
    analysis['formulas'] = {name: dict(pairwise_concordance=ranking([r['scores'][name] for r in rows], labels),
        confusion=confusion([r['scores'][name] >= 0.25 for r in rows], labels)) for name in rows[0]['scores']}
    mixed = {}
    for key in ('product', 'vector'):
        groups = {}
        for name, row in cases.items():
            value = row['scores']['product'] if key == 'product' else tuple(row['components'].values())
            groups.setdefault(value, []).append(name)
        mixed[key] = [names for names in groups.values() if len({cases[n]['harm'] for n in names}) > 1]
    analysis['mixed_harm_collisions'] = mixed
    analysis['lost_vector_distinctions'] = [
        [a, b] for i, a in enumerate(cases) for b in list(cases)[i + 1:]
        if cases[a]['scores']['product'] == cases[b]['scores']['product']
        and cases[a]['components'] != cases[b]['components']]
    return analysis


def collect():
    parameters = json.loads((EVIDENCE / 'parameters.json').read_bytes())
    config = {p['parameter_id']: p['value'] for p in parameters}
    data = json.loads((ROOT / 'scenarios/paymentco/scenario.json').read_bytes())
    cases = boundary_cases()
    for world_id in ('world_a', 'world_b'):
        rules = world_from_data(data, world_id, config['recovery_delay'])
        for seed in range(16):
            workload = generate_workload(rules, seed=seed, arrival_window=config['arrival_window'])
            for control in ('unsafe', 'safe', 'no_traffic', 'zero_duplicate_exposure'):
                selected_rules = replace(rules, duplicate_probability=0) if control == 'zero_duplicate_exposure' else rules
                selected_workload = () if control == 'no_traffic' else workload
                key = f'{world_id}/{seed}/{control}'
                cases[key] = annotated(data, selected_rules, selected_workload,
                    'safe_fixed' if control == 'safe' else 'unsafe_fixed', record_for(key))
    labels = [r['harm'] for r in cases.values()]
    sensitivity = []
    for window in (4, 16, 64):
        for cap in (1, 4, 16):
            for exponent in (0.5, 1, 2):
                values = []
                for row in cases.values():
                    raw = row['assumption']
                    record = AssumptionExposure(**{**raw, 'propagated_to': tuple(raw['propagated_to']),
                                                  'source_ids': tuple(raw['source_ids'])})
                    c = diagnostic(record, window=window, cap=cap)
                    values.append(c.impact ** exponent * c.uncertainty ** exponent * c.propagation * c.persistence)
                sensitivity.append(dict(age_window=window, propagation_limit=cap, impact_uncertainty_exponent=exponent,
                    pairwise_concordance=ranking(values, labels), confusion=confusion([v >= 0.25 for v in values], labels)))
    correlated = (record_for('a', source_ids=('x',)), record_for('b', source_ids=('x', 'y')),
                  record_for('c', source_ids=('y',)))
    correlation = asdict(assumption_debt(correlated + (correlated[0],), now_tick=16, age_window=16, propagation_limit=1))
    controls = dict(diagnostics_preserve_history=all(r['diagnostic_preserved_history'] for r in cases.values()),
        high_debt_no_traffic_no_damage=cases['no_traffic']['scores']['product'] == 1 and not cases['no_traffic']['harm'],
        same_debt_harmful_harmless=cases['harmful']['components'] == cases['transient']['components'] and not cases['transient']['harm'],
        newborn_zero_debt_can_harm=cases['newborn_harm']['scores']['product'] == 0 and cases['newborn_harm']['harm'],
        correlation_not_independent=correlation['naive_total'] == 3 and correlation['grouped_total'] == 1,
        harmless_reversible_low_impact=not cases['reversible_low_impact']['harm'])
    paths = ['experiments/assumption_debt_ablation.py', 'experiments/paymentco_slice.py',
        'scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
        'src/agent_empires/application/services.py', 'src/agent_empires/application/scenarios.py',
        'research/experiments/AE-014/protocol.md', 'research/experiments/AE-014/parameters.json']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/agent_empires/simulation').glob('*.py'))]
    return dict(model_version=MODEL, python=platform.python_version(), rng_scheme=RNG_SCHEME,
        inputs={p: sha(ROOT / p) for p in paths}, parameters=parameters, cases=cases,
        controls=controls, failed_controls=[k for k, v in controls.items() if not v],
        analysis=analyze(cases), sensitivity=sensitivity, correlation=correlation,
        incident_free_unsafe_seeds={world: [seed for seed in range(16) if not cases[f'{world}/{seed}/unsafe']['harm']]
                                   for world in ('world_a', 'world_b')},
        limitations=['Authored scales and labels, not calibrated probabilities or empirical organizational evidence.',
            'Duplicate incidents only; debt does not diagnose abandonment, costs, fitness or a causal remedy.',
            'Component vector also omits behavior/exogenous exposure; identical vectors can have different harm.',
            'Grouping maxima can undercount distinct harms with shared source; undeclared dependence remains unknown.',
            'No player comprehension, independent domain acceptance, integration or publication tested.'])


def author(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('results.json', 'timing.json'):
        if (directory / name).exists():
            raise FileExistsError('refusing to overwrite evidence: ' + str(directory / name))
    for name in ('protocol.md', 'parameters.json'):
        expected = (EVIDENCE / name).read_bytes()
        target = directory / name
        if target.exists() and target.read_bytes() != expected:
            raise ValueError('saved protocol/parameters differ')
        if not target.exists():
            target.write_bytes(expected)
    start = time.perf_counter()
    result = collect()
    (directory / 'results.json').write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n')
    budget = next(p['value'] for p in result['parameters'] if p['parameter_id'] == 'wall_budget')
    elapsed = time.perf_counter() - start
    timing = dict(elapsed_seconds=elapsed, budget_seconds=budget, passed=elapsed <= budget)
    (directory / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
    if result['failed_controls'] or not timing['passed']:
        raise RuntimeError('failed controls or timing budget: ' + str(result['failed_controls']) + str(timing))
    return timing


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    if platform.python_version() != '3.12.13':
        raise RuntimeError('selected CPython 3.12.13 required')
    if args.verify_against:
        for name in ('protocol.md', 'parameters.json'):
            if (args.verify_against / name).read_bytes() != (EVIDENCE / name).read_bytes():
                raise ValueError('reviewed protocol/parameters differ')
        with tempfile.TemporaryDirectory() as temp:
            timing = author(Path(temp))
            if canonical_json(json.loads((Path(temp) / 'results.json').read_bytes())) != canonical_json(
                    json.loads((args.verify_against / 'results.json').read_bytes())):
                raise ValueError('canonical results differ')
        print(f"PASS: canonical results reproduced without overwriting evidence; fresh {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s")
    else:
        timing = author(args.output_dir)
        print(f"PASS: authored diagnostic matrix; {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s")


if __name__ == '__main__':
    main()
