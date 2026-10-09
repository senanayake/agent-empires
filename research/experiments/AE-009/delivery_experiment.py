"""Reproducible deterministic delivery evidence; never overwrite reviewed output."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile
from importlib.metadata import version

from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.simulation.events import canonical_json

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / 'scenarios/paymentco/scenario.json'


def run_case(name):
    data = json.loads(INPUT.read_bytes())
    actor = next(a for a in data['actors'] if a['actor_id'] == 'jin')
    actor.update(profile_id='human' if name == 'human_profile' else 'implementer',
                 kind='human' if name in ('human_profile', 'matched_human') else 'agent')
    if name == 'private_world_control':
        next(p for p in data['parameters'] if p['parameter_id'] == 'a.transient_recovery')['value'] = 0
    for case, decision_id, option in [('adaptive_refusal', 'retry_count', 'adaptive'),
                                      ('category_refusal', 'retryable_types', 'selected_categories')]:
        if name == case:
            ranking = next(p for p in data['profiles'][1]['preferences'] if p['decision_id'] == decision_id)['options']
            ranking.remove(option)
            ranking.insert(0, option)
    raw = (json.dumps(data, indent=2) + '\n').encode()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'scenario.json'
        path.write_bytes(raw)
        engine = DeliveryService(load_scenario(path), run_id='ae009-delivery')
    initial = engine.history.canonical_bytes()
    commands = [dict(op='start', actor_id='jin', command_id='work.retry',
                     defect='omit_retries' if name == 'implementation_defect' else None)]
    result = {'variant_input_sha256': hashlib.sha256(raw).hexdigest(), 'ordered_commands': commands}
    try:
        job = engine.start('jin', command_id='work.retry', defect=commands[0]['defect'])
    except ValueError as error:
        result.update(rejected=str(error), state_unchanged=engine.history.canonical_bytes() == initial,
                      resource_cost=engine.spent_resource_units, pending=engine.clock.pending_count)
    else:
        commands.append(dict(op='step'))
        verification = engine.step()
        proposal = verification.proposal
        result.update(started_tick=job.started_tick, completed_tick=proposal.completed_tick,
                      resource_cost=engine.spent_resource_units, proposal=asdict(proposal),
                      unsupported_refs=[r.as_dict() for r in proposal.unsupported_decisions],
                      checks=[dict(asdict(c), passed=c.passed) for c in verification.checks],
                      assessments=[asdict(a) for a in verification.assessments])
    result['history'] = json.loads(engine.history.canonical_bytes())
    result['history_sha256'] = hashlib.sha256(engine.history.canonical_bytes()).hexdigest()
    return json.loads(json.dumps(result))


def run():
    names = ('human_profile', 'implementer', 'matched_human', 'implementation_defect',
             'private_world_control', 'adaptive_refusal', 'category_refusal')
    cases = {name: run_case(name) for name in names}
    repeat = {name: run_case(name) for name in names}
    controls = dict(
        repeated_results_equal=canonical_json(cases) == canonical_json(repeat),
        matched_kind_histories_equal=cases['implementer']['history_sha256'] == cases['matched_human']['history_sha256'],
        private_world_histories_equal=cases['implementer']['history_sha256'] == cases['private_world_control']['history_sha256'],
        faster_profile_finishes_sooner=cases['implementer']['completed_tick'] < cases['human_profile']['completed_tick'],
        explicit_nonzero_cost=cases['implementer']['resource_cost'] == 2,
        defect_detected=next(a['status'] for a in cases['implementation_defect']['assessments']
                             if a['dimension'] == 'verification_status') == 'fail',
        refusal_atomic=all(cases[n]['state_unchanged'] and cases[n]['resource_cost'] == cases[n]['pending'] == 0
                           for n in ('adaptive_refusal', 'category_refusal')),
        unassessed_dimensions_unknown=all(a['status'] == 'unknown'
            for case in cases.values() for a in case.get('assessments', [])
            if a['dimension'] not in ('implementation_conformance', 'verification_status')),
    )
    assert all(controls.values()), controls
    data = json.loads(INPUT.read_bytes())
    inputs = ['scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json', 'uv.lock',
              'src/agent_empires/application/scenarios.py', 'src/agent_empires/application/services.py',
              'src/agent_empires/simulation/artifacts.py', 'src/agent_empires/simulation/assurance.py',
              'research/experiments/AE-009/delivery_experiment.py']
    return dict(model_version='retry-plan-v1', scenario_version=data['scenario_version'],
                input_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs},
                runtime={'python': platform.python_version(), 'pytest': version('pytest')},
                root_seed=None, seeds=[], rng_usage='none; deterministic delivery, no world draws',
                parameter_provenance=[p for p in data['parameters']
                    if p['parameter_id'].startswith(('retry.', 'backoff.')) or '.work_' in p['parameter_id']],
                cases=cases, controls=controls, failed_controls=[k for k, v in controls.items() if not v],
                negative_findings=['Human profile selects zero retries and still passes chosen-spec verification.',
                                   'All inferred choices remain unsupported despite green conformance.',
                                   'Omitted retries fail implementation conformance, with validation still unknown.',
                                   'Adaptive/category choices reject pending explicit refinement.'],
                limitations=['Toy speed/cost and rules, no empirical calibration or real code generation.',
                             'Finite checks are dependent on pinned choices, not independent validation.',
                             'No payment traffic, outcomes, deployment, availability/capacity or feedback learning.',
                             'No human participants, usability, security scanning, architecture acceptance, integration or publication.'])


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--verify-against', type=Path)
    args = parser.parse_args()
    result = json.loads(json.dumps(run()))  # tuples become canonical JSON arrays
    if args.verify_against:
        assert canonical_json(result) == canonical_json(json.loads(args.verify_against.read_bytes())), 'evidence differs'
        print('PASS: canonical delivery evidence reproduced; all controls pass')
    else:
        with args.output.open('x') as output:
            json.dump(result, output, indent=2)
            output.write('\n')
        print('PASS: authored delivery evidence; all controls pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
