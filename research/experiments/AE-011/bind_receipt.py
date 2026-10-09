"""Bind the honest deferred AE-011 review after authored files settle."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / 'research/experiments/AE-011'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inputs = [
    'AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md', 'docs/model-assumptions.md',
    'docs/adr/README.md', 'docs/adr/0001-python-authority.md', 'scenarios/paymentco/README.md',
    'scenarios/paymentco/scenario.json', 'docs/campaigns/mvp/README.md',
    'docs/campaigns/mvp/campaign.json', 'docs/campaigns/mvp/evidence/AE-010.json',
    'research/experiments/AE-010/causal-traces.json', 'research/experiments/AE-010/runs.json',
    'research/experiments/AE-010/protocol.json', 'research/experiments/AE-010/review.md',
    'research/experiments/AE-010/operator-review.md', 'experiments/paymentco_slice.py',
    'src/agent_empires/application/services.py', 'src/agent_empires/simulation/outcomes.py',
    'src/agent_empires/simulation/decisions.py', 'src/agent_empires/simulation/events.py',
    'pyproject.toml', 'uv.lock', 'experiments/trace_report.py', 'tests/unit/test_trace_report.py',
    'research/experiments/AE-011/protocol.md',
]
artifacts = []
for path in sorted(DIRECTORY.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name == 'receipt-integrity.json':
        continue
    relative = str(path.relative_to(ROOT))
    if path.suffix == '.md':
        kind = 'domain_review' if path.name in ('protocol.md', 'observations.md', 'decision.md') else 'manual_check'
    elif 'packet' in relative:
        kind = 'experiment_result'
    elif path.name in ('focused-tests.json', 'full-suite.json') or 'red.json' in path.name or 'green.json' in path.name:
        kind = 'test_result'
    else:
        kind = 'manual_check'
    artifacts.append(dict(path=relative, sha256=sha(path), kind=kind))
receipt = dict(
    schema_version=1, activity_id='AE-011', outcome='defer',
    summary='Delivered tested causal text rendering and a reproducible neutral reader packet from actual AE-010 histories, with separate audit views. Zero actual reader responses; the human gate is deferred, not passed. No simulation mechanism removed or added.',
    reviewer='Assigned Codex worker self-review; no human participants or independent domain reviewer',
    review_notes='Read actual AE-010 source, retained causal histories, protocol and worker/operator limitations; predecessor check passes. Reviewed typed ancestor ordering, positive/negative access cases, unknown roots, observation timing, absent/conflicted support and historical pins. Actual red/green records and 15 focused / 312 full-suite passes are retained. Study protocol and raw response template are ready, but no participant evidence exists. Receipt outcome stays defer; the required activity checker intentionally fails. Hash integrity does not establish authenticity, comprehension, architecture acceptance, integration or publication. Local delivery is reported separately; any actual error remains in delivery.json.',
    inputs={p: sha(ROOT / p) for p in inputs}, artifacts=artifacts,
    limitations=[
        'No actual participant data supplied: participants is empty, zero sessions/readbacks, and the three-reader/two-success gate remains unmet. No human-study artifact is claimed.',
        'Engineering passes and worker self-review do not establish reader comprehension, engagement, fun, human/domain acceptance or empirical calibration.',
        'Boundary histories were deliberately selected for one harmful and one harmless unsupported choice; they are not representative workloads or statistical evidence.',
        'All six choices lack support; reader attribution to idempotency rather than other gaps is a pending test, not a finding.',
        'No Sarah replacement or information-loss event exists in the selected histories; the larger replacement story remains untested.',
        'The study delivery-desk allowlist is not the future actor snapshot/permission API. Hidden outcome/incident ancestry stays unavailable rather than inventing observed causal links.',
        'Initial missing module, omitted observation pins and mismatched support vocabulary failed checks; all raw negatives remain alongside fixes. Initial preparation wording is archived separately.',
        'No independent architecture acceptance, controller integration, publication, successor execution or campaign completion is claimed.',
        'Required local delivery failed on the single staging attempt: shared Git metadata is read-only. delivery.json preserves exit 128. No commit, retry or push occurred; operator hash-reviewed delivery recovery is required.',
    ], participants=[],
)
(ROOT / 'docs/campaigns/mvp/evidence/AE-011.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'Bound deferred receipt: {len(inputs)} inputs, {len(artifacts)} artifacts, zero participants')
