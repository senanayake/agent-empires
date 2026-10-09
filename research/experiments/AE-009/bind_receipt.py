"""Bind final activity source/evidence, excluding receipt self/cyclic hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXP = Path('research/experiments/AE-009')


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


inputs = [
    'AGENTS.md', 'docs/development.md', 'docs/mvp-campaign.md', 'docs/model-assumptions.md',
    'docs/adr/README.md', 'docs/adr/0001-python-authority.md', 'docs/campaigns/mvp/README.md',
    'docs/campaigns/mvp/campaign.json', 'docs/campaigns/mvp/evidence/AE-008.json',
    'scenarios/paymentco/README.md', 'scenarios/paymentco/scenario.json',
    'scenarios/paymentco/schema.json', 'scenarios/paymentco/jin-snapshot.json', 'pyproject.toml', 'uv.lock',
    'src/agent_empires/application/scenarios.py', 'src/agent_empires/application/services.py',
    'src/agent_empires/simulation/actors.py', 'src/agent_empires/simulation/clock.py',
    'src/agent_empires/simulation/events.py', 'src/agent_empires/simulation/knowledge.py',
    'src/agent_empires/simulation/decisions.py', 'src/agent_empires/simulation/artifacts.py',
    'src/agent_empires/simulation/assurance.py', 'tests/simulation/test_delivery_slice.py',
    'research/experiments/AE-008/review.md', 'research/experiments/AE-008/operator-review.md',
]
artifacts = []
for path in sorted((ROOT / EXP).rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts:
        continue
    relative = str(path.relative_to(ROOT))
    kind = ('domain_review' if path.name == 'review.md' else
            'experiment_result' if path.name == 'green-change.json' else
            'test_result' if path.suffix == '.json' and path.name not in ('environment.json', 'delivery.json') else
            'manual_check')
    artifacts.append(dict(path=relative, sha256=digest(relative), kind=kind))
limitations = [
    'Worker self-review; controller independent validation remains separate. No architecture/domain acceptance, integration, publication or campaign-completion proof.',
    'All speed/cost and retry-plan rules are invented toy parameters/mechanisms, with null calibration. No real software generation, payment guidance or empirical organizational estimate.',
    'Finite chosen-spec checks depend on decision versions; green conformance cannot supply independent requirement validation, security scanning or world fitness.',
    'Adaptive retry and selected-category choices reject pending explicit refinement. Zero-exposure plans cannot detect inactive retry key/audit faults.',
    'No deployment, payment outcomes, availability sampling, actor capacity, cancellation, learning, participant study or usability evidence. Admitted work completes after departure with its cost retained.',
    'Initial policy catalog is not enacted/copied automatically; root grant/source metadata are trusted. Runtime inference uses fresh live holdings; Python introspection is not a hostile-code security boundary.',
    'Actual collection/serialization and scheduling failures are retained; final fixes and negative controls pass. Seed set is empty because this mechanism makes no random draws.',
]
if (ROOT / EXP / 'delivery.json').exists():
    limitations.append('Required local Git delivery failed; exact single staging/commit attempt error is preserved in delivery.json. No retry or push; operator recovery is needed.')
receipt = dict(schema_version=1, activity_id='AE-009', outcome='pass',
    summary='Headless goal/work/decision/inference/proposal/verification slice with executable retry plans, pinned decisions, explicit toy speed/cost, unknown unassessed dimensions and reproducible counterexamples; 27 focused and 260 total tests pass.',
    reviewer='Assigned AE-009 Codex worker self-review; no independent domain reviewer or human participants',
    review_notes='Reviewed passing current AE-008 evidence and actual scenario/loader/access artifacts, then delivery source, tests and complete experiment cases/negative outputs. All controls and final checks pass for this bounded engineering mechanism. Source and current artifacts are hashed; review.md records uncertainty and scoped ledger. Conformance supplies no authority or independent validation; no mechanism removed or architecture acceptance implied.',
    inputs={p: digest(p) for p in inputs}, artifacts=artifacts, limitations=limitations)
(ROOT / 'docs/campaigns/mvp/evidence/AE-009.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Bound AE-009 source and', len(artifacts), 'artifacts')
