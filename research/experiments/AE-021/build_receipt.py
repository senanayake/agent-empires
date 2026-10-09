"""Bind settled AE-021 source/results; checker logs stay outside self-binding."""
import hashlib
import json
from pathlib import Path

root = Path('.')
experiment = Path('research/experiments/AE-021')
receipt = Path('docs/campaigns/mvp/evidence/AE-021.json')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

input_paths = [
    'AGENTS.md', 'docs/mvp-campaign.md', 'docs/model-assumptions.md',
    'docs/campaigns/mvp/campaign.json', 'docs/campaigns/mvp/README.md',
    'docs/campaigns/mvp/revisions/2026-10-09-window-milestone.md',
    'docs/campaigns/mvp/evidence/AE-020.json',
    'docs/adr/0001-python-authority.md', 'docs/adr/template.md',
    'docs/adr/README.md', 'docs/adr/0002-godot-presentation.md',
    'docs/development.md', 'docs/transport-contract.md', '.gitignore',
    'scenarios/paymentco/README.md', 'scenarios/paymentco/scenario.json',
    'scenarios/paymentco/schema.json', 'pyproject.toml', 'uv.lock',
    'src/agent_empires/application/commands.py',
    'src/agent_empires/application/services.py',
    'src/agent_empires/application/scenarios.py',
    'src/agent_empires/adapters/transport/http.py',
    'src/agent_empires/simulation/actors.py',
    'src/agent_empires/simulation/communication.py',
    'src/agent_empires/simulation/clock.py',
    'src/agent_empires/simulation/events.py',
    'src/agent_empires/simulation/randomness.py',
    'tests/contracts/test_transport.py',
    'research/experiments/AE-020/operator-review.md',
    'research/experiments/AE-020/operator-loopback-measurement.json',
]
artifacts = []
for path in sorted([*experiment.rglob('*'), *Path('godot').rglob('*')]):
    if not path.is_file() or '__pycache__' in path.parts or '.godot' in path.parts or path.suffix == '.uid':
        continue
    # Receipt checks reference this receipt; keep their raw outputs outside its hash graph.
    if path.name.startswith('activity-evidence'):
        continue
    kind = 'manual_check'
    if path.name == 'review.md':
        kind = 'domain_review'
    elif path.suffix == '.json' and path.name not in ('environment.json', 'AE-020.json'):
        kind = 'experiment_result' if 'fixtures' in path.parts else 'test_result'
    artifacts.append(dict(path=str(path), sha256=digest(path), kind=kind))
limitations = [
    'Worker cannot create kernel loopback sockets: live-headless.json retains PermissionError; real live HTTP consumption/recovery must be independently validated.',
    'X11 and Wayland display access fail in this sandbox: no visible window, viewport PNG or observed text-legibility pass is claimed. Operator live launch and viewport inspection remain pending.',
    'Headless import exits zero with sandbox editor socket-listener errors. Temporary writable XDG directories remove user-directory write errors; original diagnostics are preserved.',
    'Small finite toy setup with three jobs and three transfers; loss_probability=1 is an authored engineering counterexample, not calibrated channel behavior. No shipping/world exposure.',
    'Read-only batch/pending-marker invariants do not prove full frame-rate independence, measured Godot latency, long-session behavior, offline packaging or process restore; AE-022 and later packets remain separate.',
    'Scrollable text panels and last-120-row event text feed; no participant comprehension/enjoyment or human review. No empirical calibration, domain/architecture acceptance, integration/publication or campaign completion.',
]
notes = (
    'Codex worker self-review examined AE-020 source, public graph projection, protocol, independently reviewed tests/real loopback measurement and passing entry hashes. '
    'Archived predecessor receipt and pre-edit shared docs. Focused smoke red fails on missing scripts; final smoke passes original IDs/order, atomic rejection, passive render time, terminal facts, resnapshot bounds and refresh-cursor race. '
    'Real Python fixture regenerates identically; complete Godot headless playback reports the final Python snapshot ID, 13 actors, three proposals and received/lost states. Four Python tests pass, including explicitly mocked cleanup; initial mock PID failure retained. '
    'Required import/probe/diff checks and receipt checker are recorded, while actual socket/display failures remain visible and no live/visual pass is invented. '
    'Receipt outcome pass means bounded source/self-review readiness under independent-validation semantics; operator must validate the actual live desktop milestone. '
    'Shared ledger outside scope was not edited; review.md is the scoped ledger. No manifest/checker edits, controls, synthetic participants, successor execution or publication.'
)
if (experiment / 'delivery.json').exists():
    delivery = json.loads((experiment / 'delivery.json').read_text())
    if delivery.get('exit_code') != 0:
        limitations.append('Required local commit unavailable: single authorized staging/commit attempt failed; exact Git error retained in delivery.json. No retry, commit, push or integration claimed.')
        notes += ' Local delivery remains failed; operator hash-reviewed delivery retry is required before successor recommendation.'
receipt.write_text(json.dumps(dict(schema_version=1, activity_id='AE-021', outcome='pass',
    summary='Passive Godot 4.7.2 public projection, real recorded fixture, nonzero smoke probe, read-only HTTP client and bounded Python-owned live-preview bootstrap. Headless projection/tests pass; live sockets/desktop inspection pending independent runtime.',
    reviewer='AE-021 Codex worker self-review; independent controller/runtime review pending',
    review_notes=notes, inputs={p: digest(p) for p in input_paths}, artifacts=artifacts,
    limitations=limitations, validation_mode='independent'), indent=2) + '\n')
print(f'Bound {len(input_paths)} inputs and {len(artifacts)} artifacts')
