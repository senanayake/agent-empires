"""Bind settled AE-013 evidence; validation output is excluded from hash cycles."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path('research/experiments/AE-013')


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


inputs = [
    'AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md',
    'docs/campaigns/mvp/README.md', 'docs/campaigns/mvp/campaign.json',
    'docs/campaigns/mvp/evidence/AE-012.json', 'docs/model-assumptions.md',
    'docs/simulation-model.md', 'docs/adr/README.md', 'docs/adr/0001-python-authority.md',
    'docs/adr/0006-context-boundaries.md', 'docs/adr/0008-decision-provenance.md',
    'scenarios/paymentco/README.md', 'scenarios/paymentco/scenario.json',
    'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
    'src/agent_empires/application/services.py', 'src/agent_empires/application/scenarios.py',
    'src/agent_empires/simulation/learning.py', 'src/agent_empires/simulation/assurance.py',
    'src/agent_empires/simulation/decisions.py', 'src/agent_empires/simulation/events.py',
    'src/agent_empires/simulation/knowledge.py', 'src/agent_empires/simulation/artifacts.py',
    'src/agent_empires/simulation/outcomes.py', 'src/agent_empires/simulation/randomness.py',
    'src/agent_empires/simulation/clock.py', 'tests/simulation/test_learning_loops.py',
]
artifacts = []
for path in sorted((ROOT / BASE).iterdir()):
    if not path.is_file() or path.name in ('activity-evidence.json', 'diff-check.json', 'final-file-check.json'):
        continue
    kind = ('domain_review' if path.suffix == '.md' else
            'experiment_result' if path.name in ('loop-traces.json', 'parameters.json', 'reproducible-experiment.json') else
            'test_result' if ('red' in path.name or 'green' in path.name or 'tests' in path.name or 'suite' in path.name) else
            'manual_check')
    relative = path.relative_to(ROOT).as_posix()
    artifacts.append({'path': relative, 'sha256': sha(relative), 'kind': kind})

limitations = [
    'Finite authored model and trusted report meanings/source roots; no empirical calibration, source authentication or real payment policy correctness.',
    'Four-sample and 0.2-margin rules are invented MA-09 thresholds, not statistical confidence or proof of a causal remedy; complete cohorts and potential sample correlation remain limits.',
    'None of sixteen seeded World B runs validates the replacement against the goal: eight future failures, six unknown results, two old-policy unknown cases with no revision.',
    'No actual participants, human comprehension/enjoyment, independent domain or architecture acceptance, integration, publication or campaign completion.',
    'Arbitrary goal discovery/alternative invention and retrospective history rewriting are outside this activity; future deployment assessment does not rewrite decision support.',
    'AE-012 passed at entry; scoped successor edits make some of its original source bindings historical. Entry receipt and model assumptions are archived without rewriting predecessor evidence.',
    'Recorded development failures include the missing APIs, no-retry fixture correction, exact float boundary, policy path bypass and trace schema-key typo.',
]
delivery = ROOT / BASE / 'delivery.json'
if delivery.exists():
    result = json.loads(delivery.read_text())
    if result['exit_code'] != 0:
        limitations.append('The single permitted local Git delivery attempt failed; delivery.json preserves the actual error. No commit or push is claimed; operator hash-reviewed delivery recovery is required.')

receipt = {
    'schema_version': 1, 'activity_id': 'AE-013', 'outcome': 'pass',
    'summary': 'Three immutable learning loops change implementation, requirement interpretation and authorized policy interpretation separately; current tests, authored histories and sixteen seeded World B controls retain negative results and old deployment meaning.',
    'reviewer': 'Assigned Codex worker self-review; no independent or human reviewer claimed.',
    'review_notes': 'Reviewed AE-012 current entry receipt, actual implementation/tests, 512-pair results and traces, protocol, limitations and independent operator review before editing; entry check passed. Reviewed finite evidence admission, source/access/authority separation, exact threshold boundary, incomplete cohorts, delayed pinning, forged assessments, policy bypass rejection and history prefixes. Focused and broader regression receipts plus canonical replay are bound. Pass covers bounded engineering evidence only; authored improvement does not hide the seeded replacement misses. ADR-006/008 remain proposed. The scoped ledger is decision.md; controller validation and delivery/integration are separate.',
    'inputs': {p: sha(p) for p in inputs}, 'artifacts': artifacts,
    'limitations': limitations, 'participants': [],
    'tdd': {'red': ['tdd-red.json', 'first-green-attempt.json', 'boundary-red.json', 'policy-boundary-red.json'],
            'green': ['mechanism-green.json', 'focused-tests.json', 'full-suite.json']},
    'validation_receipts': [str(BASE / p) for p in ('focused-tests.json', 'activity-evidence.json', 'diff-check.json', 'reproducible-experiment.json', 'full-suite.json')],
}
(ROOT / 'docs/campaigns/mvp/evidence/AE-013.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'Bound {len(inputs)} inputs and {len(artifacts)} artifacts; reviewer: worker self-review')
