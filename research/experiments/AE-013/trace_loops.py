"""Author or verify deterministic engineering traces without replacing evidence."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.assurance import assess_production
from agent_empires.simulation.decisions import EvidenceUse
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem
from agent_empires.simulation.learning import Learning
from agent_empires.simulation.outcomes import PaymentInput, PaymentOutcomes, WorldRules, generate_workload

ROOT = Path(__file__).resolve().parents[3]
SCENARIO = ROOT / 'scenarios/paymentco/scenario.json'


def setup(run):
    service = DeliveryService(load_scenario(SCENARIO), run_id=run)
    return service, Learning(service.knowledge, service.authority, service.clock, service.history)


def choose(service, name, option, actor='jin', grant=None):
    return service.decisions.select(name, option, actor_id=actor,
        expected_version=len(service.decisions.versions(name)), tick=service.clock.now,
        command_id=f'{name}.{len(service.decisions.versions(name))}', correlation_id='trace',
        reason='authored trace interpretation', grant_id=grant)


def finish(service, command, defect=None):
    service.start('jin', command_id=command, defect=defect)
    return service.step()


def drain(engine):
    while engine.step() is not None:
        pass


def review(service, engine, deployment, command):
    return assess_production(service.history, deployment.ref, service.goal,
        tuple(e.event_id for e in engine.observations if deployment.ref in e.entities),
        tick=service.clock.now, command_id=command, minimum_samples=4, revision_margin=0.2)


def payload(service, learning, prefix, **extra):
    assert service.history.events[:len(prefix)] == prefix
    return {'records': [asdict(r) for r in learning.records],
            'retained_prefix_events': len(prefix), 'history_prefix_unchanged': True,
            'goal': asdict(service.goal), 'history': [e.as_dict() for e in service.history.events], **extra}


def traces():
    service, learning = setup('implementation')
    choose(service, 'retry_count', 'three')
    broken = finish(service, 'broken', 'omit_retries')
    prefix = service.history.events
    fixed = finish(service, 'fixed')
    learning.record_implementation_fix(broken.proposal, fixed.proposal,
                                       service.behavior_parameters, command_id='learn.fix')
    implementation = payload(service, learning, prefix,
                             before_checks=[asdict(c) for c in broken.checks],
                             after_checks=[asdict(c) for c in fixed.checks])

    service, learning = setup('requirement')
    choose(service, 'retryable_types', 'all_failures')
    choose(service, 'retry_count', 'one')
    choose(service, 'backoff', 'fixed')
    old = choose(service, 'idempotency', 'new_key')
    proposal = finish(service, 'unsafe').proposal
    prefix = service.history.events
    item = KnowledgeItem('interface.report', 1, 'idempotency', 'stable_key')
    service.knowledge.register_item(item)
    service.knowledge.record_holding(KnowledgeHolding('interface.report', item.ref,
        HolderRef('actor', 'jin'), ('independent-interface-contract',), 'medium', 'current'),
        tick=service.clock.now, command_id='receive.interface', correlation_id='trace')
    revised = learning.revise_requirement(service.decisions, 'idempotency', 'stable_key',
        evidence=(EvidenceUse('interface.report', old.ref, 'stable_key', 'supports', 'report', 'usable'),),
        actor_id='jin', expected_version=1, command_id='learn.requirement')
    corrected = finish(service, 'safe').proposal
    rules = WorldRules('authored-ambiguous', (0, 0, 0, 1), (0, 0, 0, 1), 1, 1, 0, 5, 1, 1)
    workload = (PaymentInput('ambiguous', 0, 'ambiguous', 0, (0, 0, 0), (0.9,) * 4),)
    engine = PaymentOutcomes(rules, service.history, service.clock)
    before = engine.ship(proposal, workload, command_id='unsafe.ship')
    after = engine.ship(corrected, workload, command_id='safe.ship')
    drain(engine)
    requirement = payload(service, learning, prefix, new_support=revised.support,
        new_authority=revised.authority_basis, before_deployment=before.ref.as_dict(),
        after_deployment=after.ref.as_dict(), results=[asdict(r) for r in engine.results])

    service, learning = setup('policy')
    choose(service, 'retryable_types', 'all_failures')
    choose(service, 'retry_count', 'one')
    choose(service, 'backoff', 'fixed')
    choose(service, 'declined_handling', 'do_not_retry', 'priya', 'grant.declined_handling')
    proposal = finish(service, 'old').proposal
    rules = WorldRules('authored-soft', (0, 1, 0, 0), (0, 1, 0, 0), 0, 1, 0.5, 20, 1, 1)
    workload = tuple(PaymentInput(f'soft{i}', 0, 'soft_decline', 0, (0, 0, 0), (0,) * 4) for i in range(4))
    engine = PaymentOutcomes(rules, service.history, service.clock)
    deployed = engine.ship(proposal, workload, command_id='old.ship')
    drain(engine)
    bad = review(service, engine, deployed, 'assess.old')
    prefix = service.history.events
    revised = learning.revise_policy(service.decisions, 'declined_handling', 'soft_only', bad,
        actor_id='priya', grant_id='grant.declined_handling', expected_version=1, command_id='learn.policy')
    future = finish(service, 'future').proposal
    future_deployed = engine.ship(future, workload, command_id='future.ship')
    drain(engine)
    good = review(service, engine, future_deployed, 'assess.future')
    policy = payload(service, learning, prefix, before_assessment=asdict(bad),
        after_assessment=asdict(good), replacement_support_before_feedback=revised.support,
        results=[asdict(r) for r in engine.results], world=asdict(rules))

    # Sensitivity evidence uses real seeded world samples within the toy model.
    # It preserves seeds where the replacement still misses the original target.
    seeded = []
    scenario = load_scenario(SCENARIO)
    parameters = {p['parameter_id']: p['value'] for p in scenario.audit_data()['parameters']}
    world = next(w for w in scenario.audit_data()['worlds'] if w['world_id'] == 'world_b')
    # Use the scenario's declared category/recovery inputs directly, with the
    # existing outcome rules and recovery delay of one tick from AE-010.
    rules = WorldRules('world_b', tuple(parameters[world['mix'][k]] for k in
        ('transient', 'soft_decline', 'hard_decline', 'ambiguous')),
        tuple(parameters[world['recovery'][k]] for k in
        ('transient', 'soft_decline', 'hard_decline', 'ambiguous')),
        parameters[world['duplicate_probability']], parameters[world['retry_cost']],
        parameters[world['abandonment_probability']], parameters[world['observation_lag']],
        parameters[world['workload_rate']], 1)
    for seed in range(16):
        service, learning = setup(f'seed-{seed}')
        choose(service, 'retryable_types', 'all_failures')
        choose(service, 'retry_count', 'one')
        choose(service, 'backoff', 'fixed')
        choose(service, 'declined_handling', 'do_not_retry', 'priya', 'grant.declined_handling')
        proposal = finish(service, 'old').proposal
        workload = generate_workload(rules, seed=seed, arrival_window=8)
        engine = PaymentOutcomes(rules, service.history, service.clock)
        old_deployed = engine.ship(proposal, workload, command_id='old.ship')
        drain(engine)
        old_review = review(service, engine, old_deployed, 'assess.old')
        result = {'seed': seed, 'old': asdict(old_review), 'future': None,
                  'workload_sha256': hashlib.sha256(json.dumps([asdict(p) for p in workload], sort_keys=True).encode()).hexdigest()}
        if old_review.assessment.status == 'fail':
            learning.revise_policy(service.decisions, 'declined_handling', 'soft_only', old_review,
                actor_id='priya', grant_id='grant.declined_handling', expected_version=1, command_id='learn.policy')
            future = finish(service, 'future').proposal
            new_deployed = engine.ship(future, workload, command_id='future.ship')
            drain(engine)
            result['future'] = asdict(review(service, engine, new_deployed, 'assess.future'))
        result['history_sha256'] = hashlib.sha256(service.history.canonical_bytes()).hexdigest()
        result['observations'] = [e.as_dict() for e in engine.observations]
        seeded.append(result)
    return {'model_version': 'learning-loops-v1', 'scenario_sha256': scenario.sha256,
            'loops': {'implementation': implementation, 'requirement': requirement, 'policy': policy},
            'seeded_world_b': seeded, 'seeded_world_rules': asdict(rules),
            'limitations': ['Authored finite reports/worlds; no empirical independence or calibration.',
                            'A goal miss is not proof of a causal remedy; negative future seeds are retained.',
                            'No independent domain/human review, integration or publication.']}


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--output-dir', type=Path)
    modes.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    encoded = json.dumps(traces(), indent=2, sort_keys=True, allow_nan=False) + '\n'
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with (args.output_dir / 'loop-traces.json').open('x') as target:
            target.write(encoded)
        print('Authored three learning loops and sixteen paired seeded controls')
    else:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'loop-traces.json'
            path.write_text(encoded)
            if path.read_bytes() != (args.verify_against / 'loop-traces.json').read_bytes():
                raise SystemExit('FAIL: canonical loop traces changed')
        print('PASS: three loop histories and sixteen seeded controls reproduce exactly')


if __name__ == '__main__':
    main()
