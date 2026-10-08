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

- All 35 queues are **pending**, with `AE-001` the designated first queue.
- No worker has been launched, no controller state database initialized, and no
  implementation or human-study result claimed by this planning task.
- Promotion is `dry_run_only`, `push: false`, with independent controller validation.
  This controls promotion; it is **not a worker-launch kill switch**.
- No remote publication, main-branch integration, deployment, hosted resources or
  scheduled automations are configured or authorized by this planning task.
- The controller's current loader does not read the top-level campaign `status`
  field. We therefore do not claim that writing `status: paused` would enforce a
  pause. Pending queues and a dry-run promotion policy are also not a substitute
  for choosing not to invoke a run command.
- No model name is pinned. Model-router review is unconfigured; `require_review_for_risk`
  is empty, and target-domain review receipts plus independent validation are
  explicit. AE-001 records a suitable worker/reviewer setup for future execution.
  The word “review” in a queue stage does not itself launch an independent reviewer.

`completion_profile: legacy` is explicit because this is a local, unstarted
planning manifest with no verified-publication authority. The controller's
`pahanna_os` profile requires an exact remote identity and publication proof; we
must not invent that authority to obtain a stronger-looking status. Legacy queue
completion is not evidence of integration, publication, or target-domain acceptance.
Before executing successors in different checkouts, verify that their predecessor
artifacts are actually present at the source revision. Never infer delivery from
a skipped/dry-run promotion receipt.

## Inspect and render now

Run from the **Agent Empires repository root**. `target_repo: .` resolves relative
to the controller process's working directory, not the manifest directory.
The environment variables below are task-specific; they do not repurpose HOME.

```bash
cd /home/senanayake/Dev/agent-empires
AE_CONTROLLER=/home/senanayake/Dev/campaign-controller
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$AE_CONTROLLER/src" \
  "$AE_CONTROLLER/.venv/bin/python" -m campaign_controller.cli inspect \
  --config docs/campaigns/mvp/campaign.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$AE_CONTROLLER/src" \
  "$AE_CONTROLLER/.venv/bin/python" -m campaign_controller.cli render-prompt \
  --config docs/campaigns/mvp/campaign.json --queue-id AE-001

python3 scripts/check_campaign.py
```

Substitute `AE-002` or `AE-003` to inspect the next recommended packets. Rendering
later packets does not run their validation commands or create their planned files.
The [planning validation receipt](validation.md) records what was actually checked.

## Future execution and evidence gates

On a future request to execute, begin with AE-001. Ensure the planning files are
available in the source revision used by the controller; an isolated Git worktree
will not inherit untracked/uncommitted files. Select the project's Python/tooling
environment and route `python3` in validation commands to it. No dependency install,
model selection or runtime setup is hidden inside this planning task.

Before a launch, the operator must establish actual predecessor integration,
reviewed allowed paths, worker/reviewer routing, promotion policy, external attempt
artifact/state locations and the next ready queue. Start with one bounded packet,
then inspect its evidence. Use the attempt orchestrator, not the legacy Codex-loop
script. Do not turn on broad auto-promotion merely to run a study. These are
execution requirements for later work, not a request for permission to finish this
planning deliverable.

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
| `participants` | For AE-011/019/029: distinct anonymized actual participant IDs, at least 3/3/5 respectively; matching human-study records are required |

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

No simulation or Godot tests can run at planning time; their named files are future
deliverables. AE-003 makes the package importable and selects the project environment
so `python3 -m pytest ...` commands work from the repository root. AE-021 selects a
specific Godot 4 editor binary and exposes it as `godot` for validation, or updates
the commands explicitly. Test scripts must exit nonzero on assertions and avoid
indefinite loops; controller commands have explicit timeouts.

The planned Godot CLI commands use the official headless, project-path, import and
script options. An import pass is only a project-load check; it does not prove
rendering or player comprehension. [Godot command-line documentation](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html).

Do not conflate the two logs: the controller records engineering attempts and
evidence; the future simulation records in-game causal events and outcomes.
