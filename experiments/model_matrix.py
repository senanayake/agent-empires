"""Bounded paired model challenge using existing authoritative domain APIs."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.paymentco_slice import run_case, world_from_data
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.assurance import assess_production
from agent_empires.simulation.communication import Channel
from agent_empires.simulation.decisions import CapabilityProfile, EvidenceUse
from agent_empires.simulation.events import canonical_json
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem
from agent_empires.simulation.learning import Clarification, Learning
from agent_empires.simulation.metrics import decision_metrics
from agent_empires.simulation.outcomes import PaymentInput, PaymentOutcomes, WorldRules, generate_workload
from agent_empires.simulation.randomness import NamedRandomness, RNG_SCHEME

EVIDENCE = ROOT / 'research/experiments/AE-015'
INPUT = ROOT / 'scenarios/paymentco/scenario.json'
CANONICAL_FILES = ('manifest.json', 'results.json')


def normalize(value):
    return json.loads(json.dumps(value, allow_nan=False))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def workload_hash(workload):
    return digest(canonical_json(normalize([asdict(p) for p in workload])))


def load_protocol():
    return json.loads((EVIDENCE / 'protocol.json').read_bytes())


def recommend_policy(blocked, soft):
    """An intervention comparison of recorded observations; no hidden world lookup."""
    left = {p['operation_id']: p['abandoned'] for p in blocked}
    right = {p['operation_id']: p['abandoned'] for p in soft}
    if left.keys() != right.keys() or len(left) != len(blocked) or len(right) != len(soft):
        raise ValueError('recommendation requires paired unique operation observations')
    return 'soft_only' if sum(right.values()) < sum(left.values()) else 'do_not_retry'


def policy_probes(data, rules, workload):
    probes = {}
    for name, strategy in (('blocked', 'declines_blocked'), ('soft', 'soft_fixed')):
        run, trace = run_case(data, rules, workload, strategy=strategy, retain_history=True)
        observations = [e['payload'] for e in trace['events'] if e['event_type'] == 'OutcomeObserved']
        if len(observations) != len(workload):
            raise ValueError('probe cohort must be completely observed')
        probes[name] = {'observations': observations, 'metrics': run['metrics'],
                        'history_sha256': run['history_sha256'],
                        'ordered_commands': run['ordered_commands']}
    probes.update(workload_sha256=workload_hash(workload),
        recommendation=recommend_policy(probes['blocked']['observations'], probes['soft']['observations']))
    return probes


def run_arm(data, rules, workload, strategy, protocol, *, kind='agent', preserve_authority=False):
    if strategy not in ('infer', 'clarify', 'feedback'):
        raise ValueError('unknown matrix strategy')
    variant = normalize(data)
    for actor in variant['actors']:
        actor['kind'] = kind
    next(a for a in variant['actors'] if a['actor_id'] == 'jin')['profile_id'] = 'implementer'
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'scenario.json'
        path.write_bytes(encoded(variant))
        service = DeliveryService(load_scenario(path), run_id='ae015-matrix')
    learning = Learning(service.knowledge, service.authority, service.clock, service.history)
    commands = []

    def select(name, option, actor='jin', grant=None):
        version = len(service.decisions.versions(name))
        command = f'choose.{name}.{version}'
        commands.append(dict(op='select', decision=name, option=option, actor=actor,
            grant=grant, expected_version=version, command_id=command, tick=service.clock.now))
        return service.decisions.select(name, option, actor_id=actor, grant_id=grant,
            expected_version=version, tick=service.clock.now, command_id=command,
            correlation_id='matrix', reason='predeclared matrix arm',
            missing_information=('world fitness unvalidated',))

    def finish(command, defect=None):
        commands.append(dict(op='start_and_finish', actor='jin', command_id=command,
                             defect=defect, tick=service.clock.now))
        service.start('jin', command_id=command, defect=defect)
        return service.step()

    if preserve_authority:
        service.authority.delegate('matrix.idempotency', 'grant.idempotency', 'ada', 'jin',
            options=('stable_key', 'new_key', 'unspecified'), tick=0,
            command_id='delegate.idempotency', correlation_id='matrix')
        commands.append(dict(op='delegate', grant='matrix.idempotency', parent='grant.idempotency',
            grantor='ada', recipient='jin', options=['stable_key', 'new_key', 'unspecified'], tick=0))
    for name, option in dict(retryable_types='all_failures', retry_count='three', backoff='fixed',
                              idempotency='new_key', audit_requirement='attempt_lineage').items():
        grant = next(g for g in data['grants'] if g['scope'] == name)
        if preserve_authority:
            select(name, option, 'jin' if name == 'idempotency' else grant['actor_id'],
                   'matrix.idempotency' if name == 'idempotency' else grant['grant_id'])
        else:
            select(name, option)
    select('declined_handling', 'do_not_retry', 'priya', 'grant.declined_handling')
    channel_cost = 0
    clarification = None
    if strategy == 'clarify':
        c = protocol['channel']
        owner = Clarification(service.knowledge, service.authority, service.clock,
                              service.history, NamedRandomness(0))  # reliable channels, no random loss
        for name, sender, recipient in (('ask', 'jin', 'ada'), ('answer', 'ada', 'jin')):
            owner.connect(Channel(name, sender, recipient, c['latency'], c['capacity'],
                                  transfer_cost=c['transfer_cost']))
        commands.append(dict(op='clarify', requester='jin', holder='ada', decision='idempotency',
                             grant='grant.idempotency', channels=c, available_at=0, command_id='query'))
        owner.ask(service.scenario.question_for('idempotency'), requester='jin', holder='ada',
            request_channel='ask', answer_channel='answer', command_id='query',
            timeout=c['timeout'], available_at=0, service_ticks=c['service_ticks'],
            grant_id='grant.idempotency')
        while (task := service.clock.pop_next()) is not None:
            owner.dispatch(task)
        owner.select('query', service.decisions, CapabilityProfile(('new_key', 'stable_key', 'unspecified')),
                     expected_version=1, command_id='clarified.choice')
        commands.append(dict(op='select_clarified', expected_version=1, command_id='clarified.choice'))
        channel_cost, clarification = owner.total_cost, asdict(owner.result('query'))
    if strategy == 'feedback':
        broken = finish('broken', 'omit_retries')
        fixed = finish('fixed')
        learning.record_implementation_fix(broken.proposal, fixed.proposal,
                                          service.behavior_parameters, command_id='learn.implementation')
        commands.append(dict(op='record_implementation_fix', before=broken.proposal.ref.as_dict(),
                             after=fixed.proposal.ref.as_dict(), command_id='learn.implementation'))
        verification = fixed
    else:
        verification = finish('work')
    engine = PaymentOutcomes(rules, service.history, service.clock)

    def expose(proposal, command):
        commands.append(dict(op='ship_and_drain', command_id=command,
            proposal=proposal.ref.as_dict(), workload_sha256=workload_hash(workload), tick=service.clock.now))
        deployment = engine.ship(proposal, workload, command_id=command)
        while engine.step() is not None:
            pass
        return deployment

    def assessment(deployment, ids, minimum, margin, command):
        commands.append(dict(op='assess_production', deployment=deployment.ref.as_dict(),
            observation_ids=list(ids), minimum_samples=minimum, revision_margin=margin,
            tick=service.clock.now, command_id=command))
        return assess_production(service.history, deployment.ref, service.goal, ids,
            tick=service.clock.now, command_id=command, minimum_samples=minimum, revision_margin=margin)

    def stage(deployment, review):
        results = [r for r in engine.results if r.deployment == deployment.ref]
        totals = {k: sum(getattr(r, k) for r in results) for k in ('completed', 'recovered',
            'abandoned', 'retry_cost', 'duplicate_charges', 'audited_attempts', 'total_attempts',
            'terminal_latency_ticks')}
        totals.update(eligible=len(workload), abandonment_rate=totals['abandoned'] / len(workload) if workload else None)
        horizon = max((r.outcome_tick - deployment.shipped_tick for r in results), default=0)
        return dict(metrics=totals, throughput_per_tick=totals['completed'] / max(1, horizon),
            ship_tick=deployment.shipped_tick, observation_tick=service.clock.now,
            fitness=dict(status=review.assessment.status, sample_count=review.sample_count,
                         abandonment_rate=review.abandonment_rate),
            decision_refs=[d.ref.as_dict() for d in deployment.proposal.decisions],
            verification={a.dimension: a.status for a in verification.assessments})

    deployed = expose(verification.proposal, 'old.ship')
    ids = tuple(e.event_id for e in engine.observations if deployed.ref in e.entities)
    review = assessment(deployed, ids, protocol['minimum_samples'], protocol['revision_margin'], 'assess.old')
    old = stage(deployed, review)
    prefix = service.history.events
    sensitivity, probes, future, policy_support = [], None, None, None
    if strategy == 'feedback':
        for minimum in protocol['sensitivity_minima']:
            for margin in protocol['sensitivity_margins']:
                for structure in protocol['evidence_structures']:
                    selected_ids = ids if structure == 'complete' else ids[:-1] if structure == 'missing_last' else ids[:1] * 8
                    assessed = assessment(deployed, selected_ids, minimum, margin,
                        f'assess.sensitivity.{minimum}.{margin}.{structure}')
                    sensitivity.append(dict(minimum=minimum, margin=margin, structure=structure,
                        status=assessed.assessment.status, sample_count=assessed.sample_count))
        # Independent interface evidence is explicit authored input, not inferred from a goal miss.
        item = KnowledgeItem('matrix.interface', 1, 'idempotency', 'stable_key')
        holding = KnowledgeHolding('matrix.interface', item.ref, HolderRef('actor', 'jin'),
                                   ('matrix.independent-interface',), 'medium', 'current')
        service.knowledge.register_item(item)
        service.knowledge.record_holding(holding, tick=service.clock.now,
            command_id='receive.interface', correlation_id='matrix')
        before = service.decisions.versions('idempotency')[-1]
        use = EvidenceUse(holding.holding_id, before.ref, 'stable_key', 'supports', 'report', 'usable')
        commands.append(dict(op='receive_report_and_revise_requirement', item=asdict(item),
            holding=asdict(holding), evidence=asdict(use), expected_version=1, command_id='learn.requirement'))
        learning.revise_requirement(service.decisions, 'idempotency', 'stable_key', evidence=(use,),
            actor_id='jin', expected_version=1, command_id='learn.requirement',
            grant_id='matrix.idempotency' if preserve_authority else None)
        probes = policy_probes(data, rules, workload)
        commands.append(dict(op='paired_observed_policy_probes', workload_sha256=workload_hash(workload),
                             recommendation=probes['recommendation']))
        if review.assessment.status == 'fail' and probes['recommendation'] == 'soft_only':
            revised = learning.revise_policy(service.decisions, 'declined_handling', 'soft_only', review,
                actor_id='priya', grant_id='grant.declined_handling', expected_version=1, command_id='learn.policy')
            policy_support = revised.support
            commands.append(dict(op='revise_policy', review=review.event_id, actor='priya',
                grant='grant.declined_handling', expected_version=1, option='soft_only', command_id='learn.policy'))
        verification = finish('future')
        future_deployed = expose(verification.proposal, 'future.ship')
        future_ids = tuple(e.event_id for e in engine.observations if future_deployed.ref in e.entities)
        future_review = assessment(future_deployed, future_ids, protocol['minimum_samples'],
                                   protocol['revision_margin'], 'assess.future')
        future = stage(future_deployed, future_review)
    latest = [service.decisions.versions(name)[-1] for name in service.work_item.required_decisions]
    metrics = decision_metrics(service.history)
    return normalize(dict(actor_kind=kind, strategy=strategy, workload_sha256=workload_hash(workload),
        world_rules=asdict(rules), closure=metrics.closure_count,
        authority_gaps=sum(d.grant_ref is None for d in latest), evidence_changes=metrics.evidence_backed_information_gain,
        idempotency=service.decisions.versions('idempotency')[-1].selected,
        policy=service.decisions.versions('declined_handling')[-1].selected,
        policy_support_at_revision=policy_support, learning_records=[asdict(r) for r in learning.records],
        history_prefix_unchanged=service.history.events[:len(prefix)] == prefix,
        old=old, future=future, channel_cost=channel_cost, work_cost=service.spent_resource_units,
        final_tick=service.clock.now, clarification=clarification, probes=probes,
        assessment_sensitivity=sensitivity, ordered_commands=commands,
        history_sha256=digest(service.history.canonical_bytes()), history=json.loads(service.history.canonical_bytes())))


def matched_projection(run):
    return {k: v for k, v in run.items() if k != 'actor_kind'}


def range_summary(values):
    return dict(mean=statistics.mean(values), min=min(values), max=max(values))


def collect(protocol):
    data = json.loads(INPUT.read_bytes())
    pairs, workloads, controls, matched = {}, {}, {}, {}
    for world in protocol['worlds']:
        rules = world_from_data(data, world, protocol['recovery_delay'])
        for seed in protocol['seeds']:
            key = f'{world}/seed-{seed}'
            workload = generate_workload(rules, seed=seed, arrival_window=protocol['arrival_window'])
            workloads[key] = normalize([asdict(p) for p in workload])
            arms = {s: run_arm(data, rules, workload, s, protocol) for s in protocol['strategies']}
            readiness = run_arm(data, replace(rules, recovery_delay=3), workload, 'feedback', protocol)
            monitoring = run_arm(data, replace(rules, observation_lag=0), workload, 'feedback', protocol)
            controls[key] = dict(workload_paired=len({r['workload_sha256'] for r in arms.values()}) == 1,
                sensitivity_workload_paired=readiness['workload_sha256'] == monitoring['workload_sha256'] == arms['feedback']['workload_sha256'],
                prefix_preserved=all(r['history_prefix_unchanged'] for r in arms.values()),
                monitoring_physics_equal=all(monitoring[s]['metrics'] == arms['feedback'][s]['metrics'] for s in ('old', 'future')),
                monitoring_recommendation_equal=monitoring['probes']['recommendation'] == arms['feedback']['probes']['recommendation'],
                closure_separate=all(r['closure'] == 6 and r['authority_gaps'] > 0 for r in arms.values()),
                inference_no_evidence=arms['infer']['evidence_changes'] == 0,
                copied_feedback_not_independent=all(r['sample_count'] <= 1 for r in arms['feedback']['assessment_sensitivity'] if r['structure'] == 'copied_first'))
            if seed == 0:
                for strategy in protocol['strategies']:
                    human = run_arm(data, rules, workload, strategy, protocol, kind='human')
                    matched[key + '/' + strategy] = matched_projection(human) == matched_projection(arms[strategy])
            # Keep full representative histories; all commands, pins and hashes remain for every seed.
            for run in [*arms.values(), readiness, monitoring]:
                if seed != 0:
                    run.pop('history')
            pairs[key] = dict(arms=arms, readiness=readiness, monitoring=monitoring,
                differences={s: {m: arms[s]['old']['metrics'][m] - arms['infer']['old']['metrics'][m]
                    for m in ('completed', 'abandoned', 'duplicate_charges', 'retry_cost', 'terminal_latency_ticks')}
                    for s in ('clarify', 'feedback')})
    boundaries = boundary_runs(data, protocol)
    analysis = {}
    for world in protocol['worlds']:
        feedback = [pairs[f'{world}/seed-{s}']['arms']['feedback'] for s in protocol['seeds']]
        delta = [r['probes']['soft']['metrics']['abandoned'] - r['probes']['blocked']['metrics']['abandoned'] for r in feedback]
        counts = {status: sum(r['future']['fitness']['status'] == status for r in feedback) for status in ('pass', 'fail', 'unknown', 'pending')}
        analysis[world] = dict(abandonment_difference=range_summary(delta), future_fitness=counts,
            recommendation='soft_only' if statistics.mean(delta) < 0 else 'do_not_retry',
            recommend_soft_seeds=[s for s, r in zip(protocol['seeds'], feedback) if r['probes']['recommendation'] == 'soft_only'],
            retain_blocked_seeds=[s for s, r in zip(protocol['seeds'], feedback) if r['probes']['recommendation'] == 'do_not_retry'],
            unrevised_seeds=[s for s, r in zip(protocol['seeds'], feedback) if r['policy'] == 'do_not_retry'],
            readiness_reversals=[s for s, r in zip(protocol['seeds'], feedback) if pairs[f'{world}/seed-{s}']['readiness']['probes']['recommendation'] != r['probes']['recommendation']],
            incident_free_inference_seeds=[s for s in protocol['seeds'] if pairs[f'{world}/seed-{s}']['arms']['infer']['old']['metrics']['duplicate_charges'] == 0],
            strategy_ranges={strategy: {metric: range_summary([pairs[f'{world}/seed-{s}']['arms'][strategy][metric] for s in protocol['seeds']])
                for metric in ('closure', 'authority_gaps', 'evidence_changes', 'channel_cost', 'work_cost', 'final_tick')}
                for strategy in protocol['strategies']},
            outcome_ranges={strategy: {metric: range_summary([pairs[f'{world}/seed-{s}']['arms'][strategy]['old']['metrics'][metric] for s in protocol['seeds']])
                for metric in ('completed', 'abandoned', 'duplicate_charges', 'retry_cost', 'terminal_latency_ticks')}
                for strategy in protocol['strategies']})
    failed = [key + '/' + name for key, row in controls.items() for name, ok in row.items() if not ok]
    failed += [key + '/actor-kind' for key, ok in matched.items() if not ok]
    failed += ['boundary/' + key for key, ok in boundaries['controls'].items() if not ok]
    return dict(model_version=protocol['model_version'], workloads=workloads, pairs=pairs,
        controls=controls, matched_kind_controls=matched, boundaries=boundaries, analysis=analysis,
        failed_controls=failed, negative_findings=[
            'A complete goal miss does not identify a causal remedy; interface report and policy probes are explicit trusted interventions.',
            'Authorized blanket policy can be mistaken; no kind conveys correctness, authority or evidence.',
            'New policies retain no independent fitness support at enactment and need separately observed cohorts.',
            'Missing feedback stays pending and repeated operation citations add no samples.',
            'Finite seed ranges are descriptive; no empirical calibration, participant evidence or general optimum.',
            'Assumption Debt scalar removed from planned gameplay; components do not replace behavior/exposure.' ])


def boundary_runs(data, protocol):
    world = WorldRules('boundary', (0, 1, 0, 0), (1, 1, 0, 1), 1, 1, 0.5, 5, 1, 1)
    soft = tuple(PaymentInput(f'p{i}', 0, 'soft_decline', 0, (0.5,) * 3, (0,) * 4) for i in range(4))
    transient = (PaymentInput('p', 0, 'transient', 0, (0,) * 3, (0,) * 4),)
    hard = (replace(transient[0], category='hard_decline'),)
    ambiguous = (replace(transient[0], category='ambiguous'),)
    runs = {name: run_arm(data, world, workload, strategy, protocol, kind=kind,
        preserve_authority=name in ('successful_autonomy', 'mistaken_human_authority')) for name, workload, strategy, kind in (
        ('no_traffic', (), 'infer', 'agent'), ('harmless_unsupported', transient, 'infer', 'agent'),
        ('hard_decline', hard, 'infer', 'agent'), ('harmful_human', ambiguous, 'infer', 'human'),
        ('successful_autonomy', soft, 'feedback', 'agent'), ('mistaken_human_authority', soft, 'infer', 'human'),
        ('stable_protection', ambiguous, 'clarify', 'agent'))}
    probes = {'recovering': policy_probes(data, world, soft),
              'nonrecovering': policy_probes(data, replace(world, recovery=(1, 0, 0, 1)), soft)}
    controls = dict(no_traffic_pending=runs['no_traffic']['old']['fitness']['status'] == 'pending',
        no_traffic_no_harm=runs['no_traffic']['old']['metrics']['duplicate_charges'] == 0,
        unsupported_harmless=runs['harmless_unsupported']['authority_gaps'] > 0 and runs['harmless_unsupported']['old']['metrics']['completed'] == 1,
        hard_decline_abandons=runs['hard_decline']['old']['metrics']['abandoned'] == 1,
        human_can_harm=runs['harmful_human']['old']['metrics']['duplicate_charges'] == 1,
        autonomous_future_passes=runs['successful_autonomy']['future']['fitness']['status'] == 'pass',
        autonomy_authorized=runs['successful_autonomy']['authority_gaps'] == 0,
        mistaken_authority_fails=runs['mistaken_human_authority']['old']['fitness']['status'] == 'fail',
        stable_key_protects=runs['stable_protection']['old']['metrics']['duplicate_charges'] == 0,
        observed_world_reversal=probes['recovering']['recommendation'] == 'soft_only' and probes['nonrecovering']['recommendation'] == 'do_not_retry',
        three_loops_distinct={r['loop'] for r in runs['successful_autonomy']['learning_records']} == {'implementation', 'requirement', 'policy'})
    return dict(runs=runs, probes=probes, controls=controls)


def source_paths():
    paths = ['experiments/model_matrix.py', 'experiments/paymentco_slice.py',
        'scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/agent_empires').rglob('*.py'))]
    return paths


def author(directory, protocol=None):
    protocol = load_protocol() if protocol is None else protocol
    directory.mkdir(parents=True, exist_ok=True)
    for name in (*CANONICAL_FILES, 'timing.json'):
        if (directory / name).exists():
            raise FileExistsError(f'refusing to overwrite evidence: {directory / name}')
    for name, raw in (('protocol.md', (EVIDENCE / 'protocol.md').read_bytes()), ('protocol.json', encoded(protocol))):
        target = directory / name
        if target.exists():
            if name == 'protocol.json':
                if canonical_json(json.loads(target.read_bytes())) != canonical_json(protocol):
                    raise ValueError('saved protocol differs')
            elif target.read_bytes() != raw:
                raise ValueError('saved protocol differs')
        else:
            target.write_bytes(raw)
    started = time.perf_counter()
    results = collect(protocol)
    manifest = dict(model_version=protocol['model_version'], python=platform.python_version(),
        rng_scheme=RNG_SCHEME, protocol=protocol,
        protocol_md_sha256=digest((directory / 'protocol.md').read_bytes()),
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in source_paths()},
        scenario_version=json.loads(INPUT.read_bytes())['scenario_version'],
        parameter_provenance=json.loads(INPUT.read_bytes())['parameters'] + protocol['parameters'],
        results_sha256=digest(canonical_json(results)),
        workload_sha256={k: digest(canonical_json(v)) for k, v in results['workloads'].items()})
    for name, value in zip(CANONICAL_FILES, (manifest, results), strict=True):
        (directory / name).write_bytes(encoded(value))
    elapsed = time.perf_counter() - started
    timing = dict(elapsed_seconds=elapsed, budget_seconds=protocol['wall_budget_seconds'],
                  passed=elapsed <= protocol['wall_budget_seconds'])
    (directory / 'timing.json').write_bytes(encoded(timing))
    if not timing['passed']:
        raise RuntimeError(f'fresh execution exceeds declared budget: {timing}')
    if results['failed_controls']:
        raise RuntimeError(f"failed engineering controls retained: {results['failed_controls']}")
    return timing


def verify(directory, protocol=None):
    protocol = load_protocol() if protocol is None else protocol
    if (directory / 'protocol.md').read_bytes() != (EVIDENCE / 'protocol.md').read_bytes():
        raise ValueError('reviewed protocol differs')
    if canonical_json(json.loads((directory / 'protocol.json').read_bytes())) != canonical_json(protocol):
        raise ValueError('reviewed protocol settings differ')
    with tempfile.TemporaryDirectory() as temporary:
        fresh = Path(temporary)
        timing = author(fresh, protocol)
        for name in CANONICAL_FILES:
            if canonical_json(json.loads((fresh / name).read_bytes())) != canonical_json(json.loads((directory / name).read_bytes())):
                raise ValueError(f'canonical evidence differs: {name}')
    return timing


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    if platform.python_version() != '3.12.13':
        raise RuntimeError('matrix requires selected CPython 3.12.13')
    timing = verify(args.verify_against) if args.verify_against else author(args.output_dir)
    print(f"PASS: canonical paired matrix; fresh {timing['elapsed_seconds']:.3f}s <= {timing['budget_seconds']}s; reviewed evidence preserved")
    return 0


if __name__ == '__main__':
    sys.exit(main())
