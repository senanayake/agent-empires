# AE-001 execution-contract review

Date: 2026-10-08. Reviewer: the assigned Codex worker (self-review, not an
independent reviewer or a human participant). Disposition: **pass for AE-001's
documentation/execution contract**, subject to the required command receipts
recorded in `docs/campaigns/mvp/evidence/AE-001.json`. No domain experiment or
architecture acceptance gate was evaluated.

## Inputs and predecessor review

The checkout started clean at `6fcef75` and contained the campaign sections 2–8,
AE-001 packet, assumptions, ADR register/template, PaymentCo brief and controller
handoff. Both the campaign and manifest give AE-001 no dependencies; no
predecessor gate receipt is required. The plan checker passed for all 35 activity
definitions. The historical planning validation explicitly does not claim to be
AE-001 evidence and is not reused as a passing activity receipt.

No root or ancestor AGENTS.md was present at entry. The new root contract routes
future workers to their exact packet, dependencies, allowed paths, commands,
timeouts, import boundary and receipt location. Configuration and the checker
are outside AE-001's write scope and remain unchanged.

## Substantive acceptance review

| Question / counterexample | Evidence and disposition |
| --- | --- |
| Could a new worker use the wrong `python3` because the controller happens to run Python 3.12? | The host command is 3.14.4, while the controller is 3.12.13. Development selects 3.12.13 explicitly, asserts its patch, and routes literal manifest commands using PATH. It requires separate setup in independent validation checkouts. The controller venv is reserved for controller commands. |
| Does a tool's presence prove a project test environment exists? | No. Host pytest 9.0.2 exists, but there is no project package, test suite or lockfile. AE-003 owns their creation; uv/`uv.lock` and the runtime are selected now. Future bootstrap and pytest commands are labeled unexecuted. |
| Could a render command silently start a worker or inspect a different checkout? | The documented commands use `inspect` and `render-prompt` from the assigned checkout with explicit controller Python/PYTHONPATH. Both exited 0. Current output shows target `.`, 35 queues, AE-001 ready, host runtime and independent validation. The original hard-coded source checkout `cd` was removed. |
| Would the old dry-run handoff protect a future operator from a launch? | No. Current campaign.json already permits local auto-promotion to `build/mvp` with push false. Controller source separates worker execution and promotion; `dry_run_only` returns a skipped promotion receipt after the attempt, not a launch veto. The handoff now names the actual policy, limits future operator execution to one queue and prohibits worker-initiated launches. |
| Does a generic instruction to push override this packet? | No. The packet and manifest explicitly disable push. Workers commit locally; the controller owns local integration and any receipts. No source branch, target branch or remote outcome is inferred from a passing worker check. |
| Can ADR-001 imply that the proposed architecture passed a review gate? | No gate is configured. Its accepted status is expressly limited to recording the existing Python-authority product constraint. The module split remains a hypothesis, import enforcement is future AE-007/020 work, and Godot/frame independence is future AE-022 evidence. The register agrees; no other ADR is promoted to accepted. |
| Could Godot own a retry rule or draw RNG because it renders a payment? | ADR-001 excludes that dependency and authority. Adapters send commands and display snapshots/events; Python owns simulation time, RNG, history and outcomes. This is a contract, not proof from unimplemented import tests. |
| Could a ledger entry or a hash check count as player or scientific acceptance? | No. The ledger records only AE-001's worker-reviewed documentation. The receipt limitations exclude participants, calibrated parameters, simulation results, integration/publication and MVP completion. The evidence contract still requires actual people for later human gates. |

## Negative findings retained

- The initial `python3 scripts/check_campaign.py --activity AE-001` exited 1
  because its receipt did not exist. The raw failure remains in observations;
  completing real documentation/evidence resolves it without changing the checker.
- Both Godot PATH lookups exited 1 with no output. This is not a claim that the
  machine contains no Godot installation. No installation was attempted.
- The earlier handoff's all-pending/no-worker/dry-run statements did not describe
  the committed execution manifest. They were reconciled in the allowed handoff;
  the planning validation remains historical and the manifest is unchanged.
- There is no independent model-router reviewer. This review is explicitly the
  author's self-review. Controller command validation is a separate subsequent
  process, not proof of independent domain acceptance.
- No simulation, replay, import-boundary, Godot, calibration or human-study tests
  were possible with this planning-only repository. No observations were invented
  to fill those gaps. No model mechanism was added, removed or calibrated.
- Local commit delivery is unavailable in this worker sandbox: `git add` exited
  128 because `/home/senanayake/Dev/agent-empires/.git/worktrees/AE-001-20261008T231933Z/index.lock`
  is on a read-only filesystem outside the writable checkout. Files remain in the
  assigned checkout, uncommitted. This is a delivery limitation, not a failed
  required content validation; the controller/operator must commit the reviewed
  files in an environment with authorized access before successor integration.

## Test method and remaining work

AE-001 changes documentation and evidence only. Behavioral TDD is not applicable;
the baseline missing-receipt failure is not presented as a newly written red
behavior test. Actual command outputs, exits and interpreter observations are
preserved in `observations.json` and the activity receipt. Controller `run --help`
supports the documented future command syntax; no launch command was executed.
No dependency environment was installed and `uv sync` is not claimed tested.

The fresh-worker walkthrough identifies AE-002 as the next recommendation only
after AE-001's artifacts are actually available and its receipt is current in
the successor checkout. AE-002 must inspect the evidence and limitations rather
than infer predecessor delivery from a dry-run or legacy completion. This worker
does not launch that successor or decide campaign completion.
