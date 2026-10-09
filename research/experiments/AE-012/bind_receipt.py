"""Bind settled AE-012 inputs/artifacts; do not hash the receipt into itself."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ACTIVITY = ROOT / 'research/experiments/AE-012'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inputs = ['AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md', 'docs/model-assumptions.md',
          'docs/adr/README.md', 'docs/adr/0001-python-authority.md', 'docs/campaigns/mvp/README.md',
          'docs/campaigns/mvp/campaign.json', 'docs/campaigns/mvp/evidence/AE-011.json',
          'docs/campaigns/mvp/revisions/2026-10-09-owner-feedback.md',
          'scenarios/paymentco/README.md', 'scenarios/paymentco/scenario.json', 'scenarios/paymentco/schema.json',
          'pyproject.toml', 'uv.lock', 'experiments/clarification_comparison.py', 'experiments/trace_report.py',
          'tests/simulation/test_clarification.py', 'src/agent_empires/application/scenarios.py',
          'src/agent_empires/application/services.py']
inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'src/agent_empires/simulation').glob('*.py'))]
artifacts = []
for path in sorted(ACTIVITY.rglob('*')):
    if not path.is_file() or path.name in ('activity-evidence.json', 'diff-check.json'):
        continue
    name = path.name
    kind = 'manual_check'
    if name.startswith(('results.', 'traces.', 'timing.')) or name.endswith('experiment.json'):
        kind = 'experiment_result'
    elif name.startswith(('tdd-', 'batch-', 'access-', 'mechanism-', 'experiment-red', 'experiment-first',
                          'authority-audit-', 'focused-tests', 'full-suite', 'final-full-suite')):
        kind = 'test_result'
    elif name in ('review.md', 'protocol.md', 'protocol.json'):
        kind = 'domain_review'
    artifacts.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), kind=kind))
limitations = [
    'Invented finite model and cost weights; no empirical calibration, real financial effect, general asking optimum or goal improvement is proven.',
    'No actual human participants/sessions; comprehension and enjoyment remain deferred to AE-029.',
    'Answers may be wrong, conflicting, stale, lost or unavailable. Holder grant validity establishes scoped rights at receipt, not truth, choice authorization or requester delegation.',
    'Reports remain rationale, not automatically independent validation; general belief/policy/goal learning remains AE-013.',
    'Workloads arrive relative to ship. Delay cost is an explicit opportunity-cost proxy, not physical predeployment customer loss.',
    'Availability is an authored earliest service tick; no shared actor service queue, source authentication, unrestricted dialogue or LLM interface is implemented.',
    'Initial implementation failures are preserved; compressed initial run is historical, while top-level results/traces bind current source. Earlier assumptions hash bindings become historical after the scoped MA-09 update.',
    'Worker self-review and local tests establish no independent architecture/domain/human acceptance, controller integration, publication or campaign completion.'
]
delivery = ACTIVITY / 'delivery.json'
if delivery.exists():
    outcome = json.loads(delivery.read_bytes())
    if outcome.get('status') == 'failed':
        limitations.append('Required local Git delivery failed on the single permitted staging/commit attempt; delivery.json preserves the actual error. Operator hash-reviewed delivery recovery is required; no retry/push occurred.')
receipt = dict(schema_version=1, activity_id='AE-012', outcome='pass',
    summary='Finite channel/availability-costed clarification and 512 paired comparisons (1,024 trajectories) preserve helpful, unavailable, wrong, conflicting, stale, out-of-scope, lossy and harmless cases. Asking changes options without manufacturing requester authority or independent validation; the sensitivity grid supports conditional benefit and retains losing seeds.',
    reviewer='Assigned Codex worker self-review; no independent or human reviewer claimed',
    review_notes='Read AE-011 actual renderer/reader materials, engineering/operator and owner-replan records; entry predecessor check passed and zero human evidence remains deferred under owner direction. Entry copies preserve the pre-edit assumptions/receipt. Reviewed answer access/lineage, integer queue boundaries, source/authority separation, negative cases and the predeclared protocol. All controls passed; 23 focused and 339 total project tests pass, and full canonical replay passes the fresh 120-second budget. See research/experiments/AE-012/review.md for figures, limits, development failures and scoped ledger. Pass covers this bounded model implementation/comparison, not a generally optimal clarification policy or empirical acceptance.',
    inputs={p: sha(ROOT / p) for p in inputs}, artifacts=artifacts, limitations=limitations, participants=[],
    tdd=dict(red=['tdd-red.json', 'batch-red.json', 'access-red.json', 'experiment-red.json', 'authority-audit-red.json'],
             green=['mechanism-green.json', 'experiment-first-check.json', 'focused-tests.json', 'final-full-suite.json']),
    validation_receipts=['research/experiments/AE-012/' + name for name in
                         ('focused-tests.json', 'reproducible-experiment.json', 'activity-evidence.json', 'diff-check.json')])
(ROOT / 'docs/campaigns/mvp/evidence/AE-012.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'Bound {len(inputs)} inputs and {len(artifacts)} artifacts; reviewer is worker self-review')
