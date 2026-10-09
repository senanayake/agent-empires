# Campaign Controller handoff

The campaign is authored for `/home/senanayake/Dev/campaign-controller` at inspected
commit `3c064387fb3bda108ff86dcddc6955a7568f22d8`. Its existing Python environment
can load the manifest. `campaign.json` is intentionally JSON: the controller's
YAML loader accepts it, its JSON schema validates it, and our local consistency
checker needs only the Python standard library. This choice does not select the
future PaymentCo scenario data format.

[The campaign document](../../mvp-campaign.md) owns domain meaning. The manifest
owns queue IDs, explicit dependencies, allowed file paths, validation commands
and stop conditions. Relevant prose fields are copied into each rendered packet;
`scripts/check_campaign.py` rejects drift between those fields. Update both when
replanning. Controller configuration and this checker should be reviewed outside
the executing worker's allowed file scope.

## Current execution state

Current owner-directed sequencing is recorded in [the approved revision](revisions/2026-10-09-owner-feedback.md). AE-011/019 are engineering/design review and study preparation; actual unfamiliar-player evidence is deferred to AE-029. For those early receipts require `acceptance_basis: engineering_and_owner_direction`, `scope_revision` referencing the bound revision document, and `human_validation: deferred_to_AE-029`. See [the build ledger](../../build-progress.md) for live local progress. The AE-001 entry-state observations below remain historical.

AE-001 reconciles this handoff with the committed manifest at source revision
`6fcef75`. The earlier [planning validation](validation.md) describes its historical
baseline; its statements about all-pending queues, dry-run promotion and no worker
launch are not the current execution policy.

- The manifest designates `AE-001` as **ready** and the other 34 queues as pending.
  This assigned AE-001 worker records its result below; it does not modify queue
  configuration, controller state or the campaign planning baseline.
- Promotion is `auto_promote_on_green`, `strategy: cherry_pick`, targeting local
  `build/mvp`, with `push: false` and independent validation before and after
  promotion. The controller owns that integration; this receipt proves no
  integration or publication. No remote push is authorized, including a worker
  branch, despite generic commit-and-push wording in rendered controller prompts.
- A `dry_run_only` promotion policy, if selected later, skips promotion; it is
  **not a worker-launch kill switch**. Inspection and rendering do not launch
  workers; the worker must not invoke `run`, `run-once` or a loop command.
- No main-branch integration, remote publication, deployment, hosted resources or
  scheduled automations are authorized by AE-001. This worker neither initializes
  nor inspects an external controller state database and makes no absence claim
  about operator-owned state.
- The controller's current loader does not read the top-level campaign `status`
  field. We therefore do not claim that writing `status: paused` would enforce a
  pause. Pending queues and a dry-run promotion policy are also not a substitute
  for choosing not to invoke a run command.
- No model name is pinned. The inspected packet uses worker profile `default`,
  controller-default model, unspecified reasoning and reviewer profile `none`.
  `require_review_for_risk` is empty. Use this setup for a bounded supervised
  packet with controller-owned independent command validation; name the actual
  evidence reviewer separately. A model-router reviewer is not configured or
  implied by a queue stage named “review.” Substantive domain/human gates still
  need their actual evidence and review before successors.

`completion_profile: legacy` is explicit for local execution without
verified-publication authority. The controller's
`pahanna_os` profile requires an exact remote identity and publication proof; we
must not invent that authority to obtain a stronger-looking status. Legacy queue
completion is not evidence of integration, publication, or target-domain acceptance.
Before executing successors in different checkouts, verify that their predecessor
artifacts are actually present at the source revision. Never infer delivery from
a skipped/dry-run promotion receipt.

### Repository activity ledger

| Activity | Repository evidence disposition | Controller disposition |
| --- | --- | --- |
| AE-001 | Execution contract recorded; worker self-review passes within its stated limits. [Receipt](evidence/AE-001.json), [observations](../../../research/experiments/AE-001/observations.json), [review](../../../research/experiments/AE-001/review.md). | Independent validation and any local promotion are controller-owned; no outcome asserted here. |
| AE-002–035 | Not executed by this worker; no participant or simulation evidence supplied. | No successor launched by AE-001. |

The next recommendation is AE-002 **after** the controller makes these committed
artifacts available in its source checkout and their receipt/review is checked.
This ledger does not decide campaign completion.

AE-001 worker delivery limitation: staging returned exit 128 because this
worktree's Git index is outside the writable sandbox on a read-only filesystem.
The worker left the completed files uncommitted for controller/operator recovery;
no worker commit, integration or publication is claimed. The receipt retains the
failure. Commit the reviewed files with authorized Git metadata access before
using them as predecessor evidence in another checkout.

## Inspect and render now

Run from the **Agent Empires repository root**. `target_repo: .` resolves relative
to the controller process's working directory, not the manifest directory.
The environment variables below are task-specific; they do not repurpose HOME.

```bash
# Start in the assigned Agent Empires checkout root; do not switch checkouts.
AE_CONTROLLER=/home/senanayake/Dev/campaign-controller
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$AE_CONTROLLER/src" \
  "$AE_CONTROLLER/.venv/bin/python" -m campaign_controller.cli inspect \
  --config docs/campaigns/mvp/campaign.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$AE_CONTROLLER/src" \
  "$AE_CONTROLLER/.venv/bin/python" -m campaign_controller.cli render-prompt \
  --config docs/campaigns/mvp/campaign.json --queue-id AE-001

# First select Python 3.12.13 as documented in docs/development.md.
python3 scripts/check_campaign.py
python3 scripts/check_campaign.py --activity AE-001
git diff --check
```

Substitute `AE-002` or `AE-003` to inspect the next recommended packets. Rendering
later packets does not run their validation commands or create their planned files.
The [AE-001 observations](../../../research/experiments/AE-001/observations.json)
record current inspect/render output. [Planning validation](validation.md) remains
historical evidence. The commands must be rerun after controller revisions;
this handoff is verified against the controller commit stated above.

## Future execution and evidence gates

The current authorization executes AE-001 only in the assigned checkout. It does
not authorize this worker to start AE-002. For an operator's next bounded execution,
ensure all predecessor artifacts and reviewed receipts are present at the actual
source revision; an isolated worktree does not inherit uncommitted files. Follow
[development](../../development.md) to select CPython 3.12.13 and route `python3`
in both worker and independent controller validation to it. AE-003 creates the
project's isolated `.venv`, `pyproject.toml` and committed `uv.lock`; until then,
planning checks need only the selected interpreter's standard library.

Before a launch, the operator must establish actual predecessor integration,
reviewed allowed paths, worker/reviewer routing, promotion policy, external attempt
artifact/state locations and the next ready queue. Start with one bounded packet,
then inspect its evidence. Use the attempt orchestrator, not the legacy Codex-loop
script. Do not turn on broad auto-promotion merely to run a study. These are
execution requirements for later work, not a request for permission to finish this
planning deliverable.

The operator's bounded command form is below. **It launches a worker and may
promote locally. It was not executed in AE-001.** Set `AE_NEXT_QUEUE` to the
reviewed ready queue (AE-002 is the recommendation, not an automatic continuation),
and set `AE_ATTEMPT_ROOT` and `AE_STATE_DB` to controller-owned absolute locations
outside worker checkouts. Use the controller environment from the inspect block,
from the intended source repository root. Verify those settings and the actual
promotion/routing/runtime policy before invocation.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$AE_CONTROLLER/src" \
  "$AE_CONTROLLER/.venv/bin/python" -m campaign_controller.cli run \
  --config docs/campaigns/mvp/campaign.json \
  --start-queue "${AE_NEXT_QUEUE:?set the reviewed queue}" --max-queues 1 \
  --worker codex-cli \
  --artifacts-root "${AE_ATTEMPT_ROOT:?set the external artifact directory}" \
  --state-db "${AE_STATE_DB:?set the external state database path}"
```

This is the attempt-orchestrator path, not `run-codex-loop` or
`scripts/run_codex_campaign.py`. Only `run --help` was checked here. One queue is
the execution limit even with `auto_promote_on_green`; inspect the resulting
controller receipts and target HEAD before recommending another queue. A pending
queue, campaign status field, legacy completion or a dry-run promotion receipt
cannot establish a safe launch boundary or delivery of predecessor artifacts.

Gates AE-007/011/015/018/019/022/029/030/035 require substantive review of the
referenced evidence before dependent work. Worker self-reported JSON is not human
acceptance. For unattended execution, bind the relevant predecessor evidence and
reviewed scope using the controller's native `decision_gate` contract/receipt hashes
on successors before launching them. No accepted decision receipts or hash pins
are fabricated now. Until such gates are configured, this manifest supports
bounded supervised execution; it does not claim to enforce independent scientific
or human acceptance automatically.

If a gate returns `narrow`, `replan`, `defer`, or `stop`, retain its negative results
and revise the campaign. Add a bounded repair/review activity and update dependent
IDs before advancing; do not simply change the outcome to `pass`. Human study
activities require actual participants; Codex can prepare, instrument, analyze and
record them but cannot supply invented participants. Recruitment/replies may be
the only legitimate external blocker in an otherwise executable packet.

Allowed paths intentionally exclude campaign configuration and the checker from
ordinary implementation packets. AE-030's eventual fix paths are unknown: update
them during the independently reviewed checkpoint once the observed finding is
known. Do not give that worker an unlimited repository write scope in advance.

## Evidence and gate contract

Each completed activity writes `docs/campaigns/mvp/evidence/<ID>.json` with:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `1` |
| `activity_id` | Exact activity ID |
| `outcome` | `pass`, `narrow`, `replan`, `defer`, or `stop`; only `pass` unlocks the current scope |
| `summary` | What was learned/delivered and whether any mechanism was removed |
| `reviewer`, `review_notes` | Who examined the evidence and a substantive explanation of the disposition; do not impersonate a human reviewer |
| `inputs` | Mapping of relevant source/scenario/protocol paths to SHA-256 hashes; do not hash the receipt itself |
| `artifacts` | List of `{path, sha256, kind}`; repository-relative files, kind one of `test_result`, `experiment_result`, `domain_review`, `human_study`, `manual_check` |
| `limitations` | Explicit list of unsupported claims, failed cases and residual uncertainty; an empty list requires justification in the review notes |
| `participants` | For AE-029: at least five distinct actual unfamiliar participant IDs and matching human-study records. AE-011/019 bind the owner-directed engineering scope revision; they do not claim participant validation |

AE-030 also cites current or retested human-study evidence. For no-change findings,
existing unchanged cohort evidence may be cited explicitly. If behavior materially
changes, collect the affected observations again and record their limits.

`python3 scripts/check_campaign.py --activity AE-007` checks current input/artifact
hashes and a passing receipt. It fails when missing, non-passing, stale or malformed.
It checks declared participant counts and referenced files, **not authenticity,
statistical sufficiency, scientific truth or quality of prose**. Independent review
must read the protocol, raw evidence, counterexamples and limitations. The
controller separately executes the required focused tests; file-existence checks
alone do not constitute domain acceptance. Historical receipts remain historical
when inputs change; AE-035 identifies which current claims need revalidation.

Experiment validation uses `--verify-against` to rerun in temporary storage and
compare canonical results with the bound evidence. It must not overwrite a reviewed
artifact before checking its hash. Runtime measurements are checked against the
declared budgets, not for byte equality with earlier wall-clock timings.

## Validation commands and tool availability

AE-001 selects CPython 3.12.13 and uv/`uv.lock`; the full setup, lock-update policy
and test commands are in [development](../../development.md). System Python is
3.14.4 and has pytest 9.0.2; that does not supply an isolated project test suite.
The controller uses its separate Python 3.12.13 environment with PyYAML 6.0.3.
No simulation or Godot tests can run yet because their files do not exist.
AE-003 makes the package importable and creates the selected project environment
so `python3 -m pytest ...` commands work from the repository root. AE-021 selects a
specific Godot 4 editor binary and exposes it as `godot` for validation, or updates
the commands explicitly. Test scripts must exit nonzero on assertions and avoid
indefinite loops; controller commands have explicit timeouts.

On the AE-001 host, `command -v godot` and `command -v godot4` both exited 1.
This proves only absence on the inspected PATH. No Godot installation was attempted.
AE-001 ran documentation/command checks, with no behavior change and no invented
red/green test cycle. The original missing-receipt failure is preserved in its
observations; final required validation results are recorded in its receipt.

The planned Godot CLI commands use the official headless, project-path, import and
script options. An import pass is only a project-load check; it does not prove
rendering or player comprehension. [Godot command-line documentation](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html).

Do not conflate the two logs: the controller records engineering attempts and
evidence; the future simulation records in-game causal events and outcomes.
