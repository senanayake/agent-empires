"""Bind settled current inputs/artifacts without hashing the receipt into itself."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'research/experiments/AE-010'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

runs = json.loads((BASE / 'runs.json').read_bytes())
inputs = list(runs['input_sha256']) + [
    'AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md', 'docs/model-assumptions.md',
    'docs/adr/README.md', 'docs/adr/0001-python-authority.md', 'docs/campaigns/mvp/README.md',
    'docs/campaigns/mvp/campaign.json', 'docs/campaigns/mvp/evidence/AE-009.json',
    'research/experiments/AE-009/review.md', 'research/experiments/AE-009/green-change.json',
    'research/experiments/AE-009/operator-retry.md', 'scenarios/paymentco/README.md',
    'tests/simulation/test_payment_outcomes.py',
]
artifacts = []
for path in sorted(BASE.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts:
        continue
    name = path.name
    if name == 'delivery.json':
        kind = 'manual_check'
    elif name == 'review.md':
        kind = 'domain_review'
    elif name in ('runs.json', 'causal-traces.json', 'timing.json') or name.endswith('.json.gz'):
        kind = 'experiment_result'
    elif name.endswith('.json') and name != 'protocol.json':
        kind = 'test_result'
    else:
        kind = 'manual_check'
    artifacts.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), kind=kind))
limitations = [
    'Worker self-review only; no independent domain/architecture acceptance, human participation, usability, integration, publication or campaign-completion evidence.',
    'Toy failed-payment workload, ordinal independent draws, readiness and resource costs; no empirical calibration or real financial guidance.',
    'Perfect delayed monitoring ignores audit-dependent/noisy detection; no arrival bursts, capacity/load coupling, cancellation, time-varying recovery, learning or policy enactment.',
    'The old blanket decline policy reverses average abandonment effect across worlds but World B seed 11 worsens; all negative, tied and incident-free seeds remain visible.',
    'Zero traffic gives an undefined abandonment rate; conformance and successful execution never establish empirical goal/requirement/security fitness.',
    'Outcome queue ownership requires quiescent delivery; external orchestration must dispatch owners correctly. Admitted proposals/deployments retain historical decisions.',
    'Predecessor register hash is historical after this authorized MA-07/08 update; exact reviewed entry bytes and passing entry check are retained.',
    'Actual serialization, monitoring-comparison and retrospective-gap failures are retained with focused red/green evidence; no parameters were tuned to hide negatives.',
]
if (BASE / 'delivery.json').exists():
    delivery = json.loads((BASE / 'delivery.json').read_bytes())
    if delivery['exit_code']:
        limitations.append('Required local Git delivery failed on the single attempt; delivery.json preserves the actual error. No commit, retry, push or successor execution is claimed; operator recovery is required.')
receipt = dict(schema_version=1, activity_id='AE-010', outcome='pass',
               summary='Explicit shipping, world-owned delayed payment outcomes and feedback, pinned incident provenance, 35 focused/295 total passing tests and 357 reproducible paired/boundary cases with reversals and harmless unsupported choices.',
               reviewer='Assigned AE-010 Codex worker self-review; no independent domain reviewer or human participants',
               review_notes='Reviewed actual AE-009 artifacts and passing entry receipt before editing. Reviewed every seeded/control result, complete representative histories, meaningful boundary/invariant/metamorphic/negative tests, protocol provenance, preserved failed comparisons and actual red/green results. Pass is bounded model consistency, not architecture or real-world acceptance. review.md records the scoped ledger and limits; Git delivery is separate.',
               inputs={p: sha(ROOT / p) for p in dict.fromkeys(inputs)}, artifacts=artifacts,
               limitations=limitations)
(ROOT / 'docs/campaigns/mvp/evidence/AE-010.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(f'Bound {len(receipt["inputs"])} current inputs and {len(artifacts)} artifacts')
