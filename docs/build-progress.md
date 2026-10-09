# Agent Empires build progress

Checkpoint: **native Godot window**, 2026-10-09 UTC, branch `build/mvp`.
The campaign controller accepted and locally integrated **AE-001–016 and
AE-020–021**. AE-017–019 have not passed; this is a passive observation preview,
not the complete playable MVP.

The [owner window milestone](campaigns/mvp/revisions/2026-10-09-window-milestone.md)
brought passive transport/rendering forward after live replacement. The approved
[early-feedback revision](campaigns/mvp/revisions/2026-10-09-owner-feedback.md)
defers unfamiliar-player evidence to the playable prototype. Audience: software
engineers, managers and other IT professionals. No participant data was invented.

## Accepted implementation

| Activities | Implemented capability | Integration commit |
| --- | --- | --- |
| AE-001–002 | Execution contract, DDD glossary, context/aggregate model and tabletop decision cases | `1e485ef`, `4a0d639` |
| AE-003 | Integer simulation clock, stable priority queue, immutable typed causal history, named seeded RNG streams | `5ac793d` |
| AE-004 | Separate actors, knowledge items/holdings, access views, tacit information loss and unreachable knowledge | `36b26e1` |
| AE-005 | Directed communication, admission limits, latency, loss/distortion and acquisition ancestry | `d2a3680` |
| AE-006 | Versioned decisions, scoped authority, independent evidence/support, inference and closure versus evidence-coverage metrics | `d660aff` |
| AE-007 | Headless composition, recorded-command replay and actor-kind metamorphic gate | `4d33f2a` |
| AE-008 | Validated JSON PaymentCo data, ten humans/five departments, optional agent profiles, hidden worlds and access projections | `3049849` |
| AE-009 | Goal/work/decision-to-proposal delivery, profile work cost/speed, behavioral verification and separate unknown correctness dimensions | `5021239` |
| AE-010 | Explicit shipping, actual payment attempts, recovery/abandonment/duplicates, delayed observations and pinned causal incident traces | `0c126fe` |
| AE-011 | Engineering-reviewed trace redaction/pins and reader-study preparation; actual player validation deferred | `4687ea8`, `39c868a`, `986ee5c` |
| AE-012 | Costed two-channel clarification with stale/wrong/conflicting/unavailable/lossy controls and 1,024 paired trajectories | `c7e1eed` |
| AE-013 | Separate implementation/interpretation/policy revision, observed-goal assessment, immutable old deployments and sixteen negative seeded controls | `c82d529` |
| AE-014 | Diagnostic-only 136-case ablation; score noninterference and counterexamples; remove scalar from gameplay | `9514a85` |
| AE-015 | 60 matched seed/world groups, infer/clarify/feedback, explicit-authority autonomy, sensitivity, preserved failed goals and model gate | `f3626f0` |
| AE-016 | Live actor replacement, separate role/function assignments, explicit authority/access/edge removal, pending-work cancellation and actual new-agent work | `361d5ef` |
| AE-020 | Versioned passive HTTP commands/snapshots/event cursors, idempotence, public redaction and recorded links/message status | `acdb997` |
| AE-021 | Native Godot 2D observation window, real Python fixture/preview owner, read-only client, scrollable assurance/event views and cleanup | `54888d4` |

The rejected Assumption Debt scalar remains diagnostic research only. Actor kind
has no moral damage rule: replacement changes actual access, authority, functions,
communication endpoints and unfinished work. Prepared matched replacements and
negative outcomes remain evidence. All parameters are authored conceptual/toy
values unless explicitly calibrated in the assumption register.

## Run and validate this checkpoint

From the repository root with the locked environment and Godot 4.7.2 on PATH:

```bash
uv sync --locked --python 3.12.13 --group dev
.venv/bin/python research/experiments/AE-021/live_preview.py
```

The normal window stays open until closed; its owner then cleans the Godot child
and local HTTP server. A finite runtime diagnostic uses `--duration 15` and
`--capture /tmp/ae021-fresh.png`; existing capture paths are refused. It must finish
all three jobs and match final displayed actor/proposal/message IDs with Python.
Python alone owns simulation time and results; Godot requests only public snapshots
and event batches. The scenario's forced-loss message is an engineering display
control, not a calibrated channel-rate claim. Nothing ships in this preview.

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q tests/contracts/test_transport.py research/experiments/AE-021/test_preview.py
godot --headless --path godot --import
godot --headless --path godot --script res://tests/smoke_probe.gd
.venv/bin/python research/experiments/AE-021/live_preview.py --verify-fixture godot/tests/fixtures/paymentco.json
.venv/bin/python scripts/check_campaign.py --activity AE-021
git diff --check
```

Observed independent checks: 524 full Python tests at AE-020; unchanged domain
source plus 43 current focused transport/bootstrap tests, Godot import/probe and
real Python fixture regeneration. Real local HTTP p95 was 0.490115 ms over 300
requests on recorded hardware. That is a small engineering workload, not a
long-session or player-usability result. Actual native runs compare 13 actor IDs,
three proposal IDs and received/lost statuses with Python.

[AE-021 operator review](../research/experiments/AE-021/operator-review.md) and
[viewport capture](../research/experiments/AE-021/operator-final-viewport.png)
record code/test/runtime/visual review. Enabled V-sync stalled native refresh/capture
on this NVIDIA host; disabling it worked. The project uses V-sync off with a
60 FPS presentation cap. Other hardware and full frame independence are unproven.
Scroll reset and historical-send state regression had actual failing probes and
were fixed. Normal-close and finite-diagnostic early-exit controls pass.

## Evidence and controller state

The requested controller at `/home/senanayake/Dev/campaign-controller`, commit
`3c064387fb3bda108ff86dcddc6955a7568f22d8`, was not edited. Live authority remains
the external durable state, not the initial repository manifest statuses:

- Config: `/home/senanayake/.local/state/agent-empires-mvp/execution.yaml`.
- Database: `/home/senanayake/.local/state/agent-empires-mvp/controller.sqlite3`.
- Attempts: `/home/senanayake/.local/state/agent-empires-mvp/artifacts/campaigns/agent-empires-mvp/attempts/`.
- Active ready successor: AE-022; no successor launched at this window checkpoint.
- Clean integration checkout: `/home/senanayake/Dev/agent-empires-mvp-integration`,
  branch `build/mvp-integration`, fast-forwarded into this `build/mvp` checkout.

Original sandbox Git/socket/display failures remain in attempt history. The root
operator independently reviewed/hash-pinned files; a fresh deterministic delivery
retry reran required checks, committed and received actual controller promotion.
The first AE-021 delivery retry correctly rejected root-bound ignored bytecode
cache references; original receipt/cache bytes and failure were preserved, and
only the evidence references were corrected. No source or gate was relaxed.

Shared-model/docs legitimately supersede older receipt inputs. AE-021 preserves
AE-020's entry receipt/docs, and earlier activities preserve their own entry
state and negative results. Use each experiment's version-bound reproduction
contract or generate fresh results; do not rehash old evidence silently. The
older AE-015 matrix remains historical after AE-016 scenario/core extensions.

All delivery is local. `main` was not advanced and no remote push occurred.
The user's original untracked `img/AgentEmpires.png` was not staged or modified.

## Remaining campaign work

AE-022 owns full frame/reconnect and latency checks. AE-017–019 still own explicit
transfer/topology/comprehension preparation before management commands. Player
actions, shipping/consequence inspection in Godot, the short game loop and genuine
participant playtests remain. The 4096-ID cache, in-memory state, longer sessions,
save/restore, packaging and broader performance remain separate activities. No
empirical calibration, comprehension/enjoyment evidence or full MVP completion
is claimed by this checkpoint.
