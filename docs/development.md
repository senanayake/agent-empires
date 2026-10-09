# Development and execution contract

Execution contract established AE-001, updated AE-003, 2026-10-08. The repository
now includes a locked Python package, clock/RNG/history primitives and focused
tests. A passive Godot preview is now available; management controls and gameplay validation remain future activities. Start with [AGENTS.md](../AGENTS.md),
then use the assigned queue's scope and commands in the
[manifest](campaigns/mvp/campaign.json). For example, AE-001 has no predecessors,
produces this execution contract, and records its receipt at
`docs/campaigns/mvp/evidence/AE-001.json`.

## Python and environment

Select **CPython 3.12.13** as the execution baseline and **uv** for environment
and lockfile management. uv 0.11.24 is the observed tool version for this contract.
The choice uses an already available interpreter without changing system Python
or borrowing the controller's installed dependencies. The table below preserves
AE-001 entry observations; current AE-003 setup is documented after it. It is a local engineering
choice, not a claim of cross-version deterministic simulation.

| Surface | Observed on this worker host | Contract |
| --- | --- | --- |
| System `python3` | `/usr/bin/python3`, CPython 3.14.4; pytest 9.0.2 importable | Useful extra checker observation; not the selected project execution baseline |
| Selected interpreter | uv-managed CPython 3.12.13 | Explicit selection and version assertion before validation |
| Controller | `/home/senanayake/Dev/campaign-controller/.venv/bin/python`, CPython 3.12.13, PyYAML 6.0.3 | Run only controller commands with this environment; do not install project packages into it |
| uv | `/home/senanayake/.local/bin/uv`, 0.11.24 | Create project environment and maintain `uv.lock` in AE-003 |
| Godot | Both `command -v godot` and `command -v godot4` returned 1 with no output | Absent from this PATH; installation elsewhere was not searched; do not install in AE-001 |
| Project package and tests | No `pyproject.toml`, `uv.lock`, `src/`, `tests/` or `godot/` at activity entry | AE-003 starts the Python package/tests; AE-021 selects a Godot 4 binary |

Raw command output is in
[observations.json](../research/experiments/AE-001/observations.json).
Recheck availability on each host; historical observations are not prerequisites
that an arbitrary host already satisfies.

### Planning checks now (AE-001 and AE-002)

Run in the **assigned Agent Empires checkout root**, not the controller repository.
Locate the existing interpreter without downloads, assert the selected patch,
and route the manifest's literal `python3` commands to it:

```bash
AE_PYTHON="$(uv --no-cache --offline python find --no-python-downloads 3.12.13)"
"$AE_PYTHON" -c 'import sys; print(sys.executable); print(sys.version); assert sys.version_info[:3] == (3, 12, 13)'
export PATH="$(dirname "$AE_PYTHON"):$PATH"
hash -r
python3 -c 'import sys; print(sys.executable); assert sys.version_info[:3] == (3, 12, 13)'
python3 scripts/check_campaign.py
python3 scripts/check_campaign.py --activity AE-001
git diff --check
```

The activity check fails before its real passing receipt exists. It is an
acceptance check, not permission to create an invented result. If the interpreter
lookup fails, record that failure and obtain the selected runtime through the
controller's authorized setup; do not silently switch the project baseline.
No package installation is needed for these standard-library checks.

### Project setup after AE-003

`pyproject.toml` pins CPython **3.12.13**, uses setuptools **82.0.1** as the
minimal established build backend, and discovers the `src/agent_empires` package.
Runtime dependencies are empty. The `dev` group pins pytest **9.1.1**; transitive
test dependencies are committed in `uv.lock`. Setuptools is a pinned isolated
build requirement, not a simulation dependency. No framework or scenario parser
is selected. This choice proves local packaging, not cross-platform installation.

From the assigned checkout root:

```bash
uv sync --locked --python 3.12.13 --group dev
source .venv/bin/activate
python3 -c 'import sys; print(sys.executable); assert sys.version_info[:3] == (3, 12, 13)'
python3 -m pytest -q tests/unit/test_clock.py tests/unit/test_event_history.py
python3 research/experiments/AE-003/replay_fixture.py --verify-against research/experiments/AE-003
python3 scripts/check_campaign.py --activity AE-003
git diff --check
```

AE-003's initial online lock attempt failed on PyPI DNS. Available uv cache
metadata/wheels were copied to a writable temporary cache, and `uv --offline`
created the real lock and synchronized the checkout's own environment. Raw setup
commands and outputs: [bootstrap-offline.json](../research/experiments/AE-003/bootstrap-offline.json).
For this worker host the successful cache override was
`UV_CACHE_DIR=/tmp/agent-empires-ae003-uv`; that temporary path is not portable.
Operators may use `--offline` with their own populated writable cache. Otherwise
normal synchronization needs package-index access. Do not substitute controller
packages, system pytest, fabricated locks or a different interpreter.

Commit `pyproject.toml` and `uv.lock` together. `.venv` is already ignored and
belongs to its checkout; never share it across worker checkouts. Ordinary setup
uses `uv sync --locked` so stale metadata fails. An intentional dependency update
uses `uv lock --python 3.12.13`, followed by locked sync and affected tests.

[AE-003 run metadata](../research/experiments/AE-003/run-manifest.json) records
source hashes/model version, fixture/scenario version/hash, initial state, ordered
commands, seeds, RNG scheme, uv, Python, platform and dependency versions.
The fixture accepts `--output-dir <fresh-directory>` to author results and
`--verify-against <evidence-directory>` to regenerate in temporary storage and
compare without overwriting reviewed evidence. Existing authored output is
refused. It is a four-command engineering fixture, not PaymentCo or save/resume.

Any runtime, draw-method or RNG-scheme upgrade changes the supported replay
contract and needs an explicit version update, fresh lock and replay evidence.
Cross-runtime replay remains unproven. Evidence input hashes become historical
when a successor legitimately updates their files; preserve and review the entry
state rather than rewriting predecessor receipts. AE-003 archives AE-002's
pre-edit register and this guide in its experiment directory.

The controller operator must ensure `python3` resolves to the selected runtime
in **each worker and independent validation checkout**, including post-promotion
validation. Activating a venv in this worker does not configure another process.
Do not change manifest commands or relax checks to compensate for missing setup.

## Test and decision workflow

Read the queue's validation list and timeouts before work. AE-001's required
commands are the activity check and `git diff --check`, each with a 30-second
budget. Also run the plan-only checker and the handoff's controller inspect/render
commands. Review documented availability against observations and ADR status
against its actual authority. The original missing receipt is preserved as a
negative baseline, not labeled a new failing behavior test.

For later behavior changes, record the focused test's actual red output before
implementation, then green output after the change and after any refactoring.
Use deterministic invariants and boundary/negative cases for unit behavior,
integration tests for command/event histories, metamorphic relabeling and paired
seeded experiments for actor/world claims. Run the focused commands in the packet;
`python3 -m pytest -q` is a broader check once a suite exists, not a substitute for
missing focused tests. Use `--verify-against` for existing experiment evidence so
retesting cannot overwrite the result being checked. Godot checks begin only
when AE-021 supplies a selected editor and a project.

Required failures prevent acceptance; optional failures remain evidence. For
controller-owned runtime setup unavailable in the worker sandbox, preserve
`not_run` receipts and follow the packet's independent-validation policy.
Documentation-only work uses real command checks and substantive review, without
tests that merely assert headings or duplicate prose.

Use [the ADR template](adr/template.md) for consequential decisions and update
[the register](adr/README.md). A recorded product constraint can be accepted as a
constraint without accepting an unimplemented architecture. Hypotheses stay
proposed until their named evidence exists. Supersede historical decisions rather
than silently replacing their rationale.

## Import boundary and evidence

[ADR-001](adr/0001-python-authority.md) fixes the authority direction:

```text
Godot / transport / persistence adapters -> application -> simulation
headless experiments ---------------------> application -> simulation
```

Simulation owns rules, integer simulated time, seeded RNG and causal history.
It cannot import application, adapters, Godot, UI, HTTP or controller code, read
live services, or use renderer frame time as domain time. Application coordinates
simulation commands. Adapters translate commands, snapshots and events; Godot
renders and sends input. The exact module split remains a hypothesis for AE-002.
Dependency enforcement and determinism tests arrive in AE-007/020/022; this
document does not claim those tests already pass.

Follow the [handoff receipt contract](campaigns/mvp/README.md#evidence-and-gate-contract).
Keep raw outputs and failed observations under `research/experiments/<ID>/`;
bind relevant inputs and artifacts by SHA-256 after final edits. Do not hash the
receipt into itself or create mutually hashed files. Identify the real reviewer
and scope of review. Hash consistency proves neither scientific validity nor
participant authenticity. Do not fabricate human evidence or claim MVP completion.

Commit only the assigned activity and hand its report back to the controller.
The [launch policy](campaigns/mvp/README.md#future-execution-and-evidence-gates)
limits operators to one reviewed packet; workers never launch successors.

## AE-021 passive Godot preview

Godot **4.7.2.stable.official.ed1daf0bf** is already on this activity's validation
PATH as `godot`; use that installed binary. Python remains checkout-local 3.12.13
with the locked environment above. No Godot installation or dependency change.

```sh
godot --headless --path godot --import
godot --headless --path godot --script res://tests/smoke_probe.gd
.venv/bin/python research/experiments/AE-021/live_preview.py --verify-fixture godot/tests/fixtures/paymentco.json
.venv/bin/python -m pytest -q research/experiments/AE-021/test_preview.py
.venv/bin/python research/experiments/AE-021/live_preview.py --duration 30 --capture /tmp/ae021-live.png
```

The last command opens the actual passive window, owns loopback server/child cleanup
and verifies Godot's final displayed IDs/statuses against Python. Existing captures
are refused. Window access and kernel sockets are required; headless import/probe
success does not establish a live window. See the [bounded preview guide and scoped
ledger](../research/experiments/AE-021/review.md) for CLI configuration, fixture-only
launch, viewport capture, inspection criteria and preserved sandbox failures.

The normal preview stays open until its window is closed or Ctrl-C is pressed:

```sh
.venv/bin/python research/experiments/AE-021/live_preview.py
```

`--duration 15` selects a finite acceptance diagnostic; these runs still require
three completions and matching final Godot/Python IDs. A normal user close in the
default `--duration 0` mode performs cleanup without claiming completion.
Godot disables V-sync and caps presentation at 60 FPS: native OpenGL stalled with
V-sync enabled on the observed NVIDIA host, while real disabled-V-sync runs
updated and captured correctly. This setting never determines Python ticks.
The 4096-command cache and bounded recovery remain preview limits; long sessions
and frame-rate/reconnect validation belong to AE-022/033.
See [independent operator review](../research/experiments/AE-021/operator-review.md)
for actual window captures, preserved negative runs and current acceptance.
