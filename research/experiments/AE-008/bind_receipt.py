"""Bind settled current files to AE-008's worker self-review receipt."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
experiment = root / 'research/experiments/AE-008'
def digest(path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()

inputs = ['AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md',
          'docs/model-assumptions.md', 'docs/adr/README.md', 'docs/adr/0010-scenario-format.md',
          'docs/simulation-model.md', 'docs/campaigns/mvp/README.md',
          'docs/campaigns/mvp/campaign.json', 'scripts/check_campaign.py',
          'docs/campaigns/mvp/evidence/AE-007.json', 'research/experiments/AE-007/decision.md',
          'research/experiments/AE-007/protocol.md', 'research/experiments/AE-007/results.json',
          'experiments/headless_probe.py', 'pyproject.toml', 'uv.lock',
          'scenarios/paymentco/README.md', 'scenarios/paymentco/schema.json',
          'scenarios/paymentco/scenario.json', 'scenarios/paymentco/jin-snapshot.json',
          'src/agent_empires/application/__init__.py', 'src/agent_empires/application/scenarios.py',
          'tests/unit/test_scenarios.py']
inputs += sorted(str(p.relative_to(root)) for p in (root / 'src/agent_empires/simulation').glob('*.py'))
artifacts = []
for path in sorted(experiment.iterdir()):
    if path.suffix not in ('.md', '.json', '.py') or path.name.startswith('final-'):
        continue
    relative = str(path.relative_to(root))
    kind = 'domain_review' if path.name == 'review.md' else 'manual_check'
    if path.name in ('tdd-red.json', 'first-implementation.json', 'review-red.json',
                     'review-green.json', 'numeric-red.json', 'focused-tests.json',
                     'full-suite.json', 'predecessor-check.json', 'predecessor-replay.json',
                     'diff-check.json', 'activity-evidence.json'):
        kind = 'test_result'
    artifacts.append(dict(path=relative, sha256=digest(relative), kind=kind))

limitations = [
    'Worker self-review only; independent controller validation and domain review remain separate. No architecture, empirical calibration, human participation, comprehension, integration, publication or campaign-completion claim.',
    'Both worlds and all 52 operational parameters are invented. No world/outcome/work/adaptive-policy/learning rule is implemented or tested here; profile cost/speed/availability and function/channel/grant data are inputs for successors.',
    'The standard-library schema evaluator implements only the bundled vocabulary, rejects unsupported assertion keywords, and is not general JSON Schema certification. Lookup assumes source layout; packaging is AE-032.',
    'Actor projections are API access boundaries, not hostile Python security. Provenance and root authority are trusted metadata, not authenticated truth/legitimacy. Snapshots describe initial state; live services must use current store views.',
    'Actual initial missing-loader red, UTF-16/future-version/public-goal regression failures, and oversized-integer conversion failure are retained alongside repaired green checks.',
    'AE-007 was passing and substantively reviewed/reproduced at entry. Legitimate ADR register/scenario brief updates make those predecessor documentation hashes historical; originals are archived, predecessor receipt/source/results were not rewritten.',
    'No YAML parser portability experiment was performed; JSON was selected using the explicitly authorized format alternative and exercised with actual inputs.',
]
if (experiment / 'delivery.json').exists():
    delivery = json.loads((experiment / 'delivery.json').read_text())
    if delivery['exit_code'] != 0:
        limitations.append('The single authorized staging/commit attempt failed; no worker commit or push. Raw Git error is in delivery.json. Local delivery requires controller/operator recovery.')

checks = []
for name in ['focused-tests', 'activity-evidence', 'diff-check']:
    path = experiment / (name + '.json')
    run = json.loads(path.read_text()) if path.exists() else None
    checks.append(dict(name=name, status=('passed' if run['exit_code'] == 0 else 'failed') if run else 'not_run',
                       command=run['command'] if run else 'python3 scripts/check_campaign.py --activity AE-008',
                       artifact_ref=str(path.relative_to(root)) if run else None,
                       notes=[run['stdout'].strip() or 'No whitespace errors'] if run else ['Receipt authored before its first checker run.']))
receipt = dict(schema_version=1, activity_id='AE-008', outcome='pass',
    summary='Authored strict JSON PaymentCo inputs, schema, scoped reference/provenance validation, initial knowledge projections, ADR-010 and model guide. Ten actors, six decisions, three optional agent profiles and two toy worlds; no mechanism removed.',
    reviewer='Assigned AE-008 Codex worker self-review; no independent domain or human reviewer',
    review_notes='Reviewed current predecessor artifacts and passing entry receipt, reproduced its canonical runs, then reviewed actual authored input/schema, loader, independent Jin projection and all red/green logs. Final 45 focused and 232 total tests pass. World changes and matched actor kind relabeling preserve access; unauthorized policy references reject. Pass covers bounded input validation only. Shared documentation evolution is archived explicitly. See research/experiments/AE-008/review.md for substantive findings, limits and scoped ledger.',
    inputs={p:digest(p) for p in inputs}, artifacts=artifacts, limitations=limitations,
    predecessor_review=dict(activity_id='AE-007', disposition='pass at entry; actual gate/trace review and canonical replay',
        artifact_refs=['research/experiments/AE-008/predecessor-check.json', 'research/experiments/AE-008/predecessor-summary.json', 'research/experiments/AE-008/predecessor-replay.json']),
    validation_environment=json.loads((experiment / 'environment.json').read_text()),
    validation_receipts=checks,
    test_method='Focused collection red, actual boundary/access regression reds and repairs; negative/unit/invariant, initial simulation-owner integration and metamorphic world/kind controls. No participant or payment-outcome experiments.',
    next_recommendation='AE-009 after local delivery, independent controller validation and evidence review')
if (experiment / 'delivery.json').exists():
    receipt['delivery'] = dict(status='uncommitted', commits=[], artifact_ref='research/experiments/AE-008/delivery.json')
    receipt['next_recommendation'] = None
(root / 'docs/campaigns/mvp/evidence/AE-008.json').write_text(json.dumps(receipt, indent=2) + '\n')
