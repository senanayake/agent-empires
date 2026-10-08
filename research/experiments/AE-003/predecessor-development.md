# Development and execution contract

AE-001, 2026-10-08. This repository currently contains planning documents and a
standard-library campaign checker. Simulation code, project dependencies and the
Godot project are future activity deliverables. Start with [AGENTS.md](../AGENTS.md),
then use the assigned queue's scope and commands in the
[manifest](campaigns/mvp/campaign.json). For example, AE-001 has no predecessors,
produces this execution contract, and records its receipt at
`docs/campaigns/mvp/evidence/AE-001.json`.

## Python and environment

Select **CPython 3.12.13** as the execution baseline and **uv** for environment
and lockfile management. uv 0.11.24 is the observed tool version for this contract.
The choice uses an already available interpreter without changing system Python
or borrowing the controller's installed dependencies. It is a local engineering
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

### Package bootstrap in AE-003 (not performed by AE-001)

AE-003 owns `pyproject.toml` and `uv.lock`. Set `requires-python = "==3.12.13"`
for this initial execution baseline, configure the `src/agent_empires` package
to be importable from the checkout, and declare pytest in the `dev` dependency
group. Select and document the minimal packaging backend then; do not introduce
a web framework, scenario parser or scientific library without an activity need.
Keep runtime dependencies minimal and put test tools in the development group.

Create the initial lock with `uv lock --python 3.12.13`, then use:

```bash
uv sync --locked --python 3.12.13 --group dev
source .venv/bin/activate
python3 -c 'import sys; print(sys.executable); assert sys.version_info[:3] == (3, 12, 13)'
python3 -m pytest -q tests/unit/test_clock.py tests/unit/test_event_history.py
```

These commands become runnable only when AE-003 creates the package and tests.
Commit `pyproject.toml` and `uv.lock` together. `.venv` is already ignored and
belongs to its checkout; never share it across worker checkouts or activate the
controller's venv for project tests. Ordinary validation uses `uv sync --locked`
so stale dependency metadata fails rather than silently refreshing the lock.
Dependency updates explicitly regenerate the lock and rerun affected tests.
Record uv, Python, platform and dependency versions with reproducibility evidence.
Any Python patch/minor upgrade changes the supported replay envelope and requires
an explicit documented update, fresh lock and replay tests. Python 3.14 support
and portable replay across runtimes remain unproven.

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
