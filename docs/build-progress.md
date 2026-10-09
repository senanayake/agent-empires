# Agent Empires build progress

Checkpoint: accepted through AE-015, 2026-10-09 UTC (2026-10-08 local), branch `build/mvp`.
This records local implementation and observed engineering results, not completion
of the playable MVP. Source of scope: [MVP campaign](mvp-campaign.md).

## Delivered and accepted

The campaign controller has accepted and locally integrated AE-001 through AE-015 under the revised scope.
Each activity has a repository evidence receipt and retained development failures,
checks and limitations. The authoritative Python core has no UI, transport,
controller or external LLM dependency.

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

## Revised AE-011 engineering checkpoint

The owner approved continuing with their design feedback and moving unfamiliar-player
validation to the playable prototype. The initial audience is software engineers,
managers and other IT professionals. [The approved scope revision](campaigns/mvp/revisions/2026-10-09-owner-feedback.md)
changes AE-011/019 to engineering/design review and preparation. Comprehension and
fun remain untested and will require genuine evidence at AE-029.

Commit `4687ea8` originally integrated engineering preparation while the earlier
three-reader gate was deferred. Its original receipt, unrun protocol, blocked
attempt and protected-Git delivery failure remain archived. Revised engineering
acceptance is based on actual code/test review and owner direction, with
`participants: []`, `human_validation: deferred_to_AE-029` and the bound revision.
The revised receipt does not claim the original unfamiliar-reader criteria passed.
A fresh bounded controller retry accepted and locally promoted the engineering scope; its original attempt remains failed. No unfamiliar-reader success is claimed.

Study materials remain ready: [reader instructions](../research/experiments/AE-011/packet/reader/instructions.md),
[facilitator protocol](../research/experiments/AE-011/protocol.md) and
[response template](../research/experiments/AE-011/response-template.md). No person
was recruited and no response or participant identity was invented. Later player
sessions retain unfamiliarity screening, neutral prompts, actual anonymized
responses, material hashes, interventions, confusion and dissent. The supplied
histories currently test inference, delivery and delayed observation; they do not
yet contain the Sarah-replacement story.

## Reproduce this checkpoint

Use the pinned CPython 3.12.13 and locked project environment, separate from the
controller environment:

```bash
uv sync --locked --python 3.12.13 --group dev
uv run --locked --python 3.12.13 --group dev python3 -m pytest -q
uv run --locked --python 3.12.13 --group dev python3 experiments/model_matrix.py --verify-against research/experiments/AE-015
uv run --locked --python 3.12.13 --group dev python3 experiments/trace_report.py --verify-against research/experiments/AE-011/packet
uv run --locked --python 3.12.13 --group dev python3 scripts/check_campaign.py
uv run --locked --python 3.12.13 --group dev python3 scripts/check_campaign.py --activity AE-015
```

The latest independent engineering run passed **442 tests** (17 focused model
matrix cases). All 60 matched seed/world groups reproduce canonical results at
14.270 seconds under the 120-second budget. [AE-015 operator review](../research/experiments/AE-015/operator-review.md)
records controls and limits. World-dependent recommendations reverse, actor kind
has no matched-state effect, and an authority-preserving all-agent boundary passes.
Most revised seeded policies still fail or remain unknown against the goal.

AE-014's 136 cases rejected the gameplay debt scalar: equal scores/vectors can
have different consequences and newborn zero persistence can harm. Diagnostics
leave histories and outcomes unchanged. Keep components with behavior/exposure;
research functions remain only for reproduction. AE-010/012/013 retain earlier
outcome, clarification and learning evidence; their source-bound manifests become
historical after legitimate successor extensions. Do not silently rehash them.
The current combined matrix and trace-rendered player packet are runnable.

The first AE-015 delivery retry failed staged whitespace checks in a raw test
log. Exact bytes remain SHA-bound in `first-green-attempt-raw.json`; the readable
copy only strips trailing spaces. No source/model result changed, and both failed
attempts remain in controller history. A fresh validated retry promoted locally.

An actual preflight found pending Sarah work still completed after departure.
[The runtime scope correction](campaigns/mvp/revisions/2026-10-09-replacement-runtime.md)
lets AE-016 add minimal public lifecycle APIs and the live application bridge.
Acceptance remains unchanged. The accepted AE-015 receipt and old planning files
are archived at `research/experiments/AE-015/runtime-scope-entry`; exactly the two
planning hashes were rebound. Model source/results/protocol are unchanged.

The revised AE-011 check means engineering acceptance only. AE-019 has the same
owner-directed engineering/design scope. Unfamiliar-player hypotheses remain
unresolved, and AE-029 still requires genuine participant evidence.

Experiments accept `--output-dir` (or the trace renderer's `--packet-dir`) for a
fresh output directory and refuse overwriting authored evidence. `--verify-against`
regenerates into temporary storage and compares. Replay is demonstrated on the
selected runtime; cross-runtime/platform replay and resumable saves are unproven.
The earlier receipts capture their activity's entry inputs. Later legitimate
shared-model/doc changes can make old bindings historical; review the archived
entry copies and findings instead of silently rehashing earlier acceptance.

## Live controller execution

The requested controller repository is `/home/senanayake/Dev/campaign-controller`,
used at commit `3c064387fb3bda108ff86dcddc6955a7568f22d8`. Its source was not edited.
Execution state is external to the project:

- Configuration: `/home/senanayake/.local/state/agent-empires-mvp/execution.yaml`.
- Durable state: `/home/senanayake/.local/state/agent-empires-mvp/controller.sqlite3`.
- Attempt artifacts: `/home/senanayake/.local/state/agent-empires-mvp/artifacts/campaigns/agent-empires-mvp/attempts/`.
- Next ready engineering activity: AE-016. Original failed attempts remain in history.
- Clean integration target: `/home/senanayake/Dev/agent-empires-mvp-integration`,
  branch `build/mvp-integration`, then fast-forwarded to this `build/mvp` checkout.

The clean target preserves the user's untracked `img/AgentEmpires.png` in the
original checkout; that image was not staged or modified. The committed campaign
manifest retains its initial statuses, and launch-time YAML can also predate the
last state transition. At this checkpoint the durable database records AE-001–015 complete, AE-016 ready and AE-017–035 pending. Neither the baseline manifest nor a worker commit
is a current acceptance ledger.

Earlier workers hit the same protected Git metadata limitation. Original attempts
and failures were preserved, then reviewed artifacts received bounded delivery
retries and actual controller validation/promotion. Local operator review records
and retry helpers are under `/home/senanayake/.local/state/agent-empires-mvp/`.
They are host-specific orchestration aids, not simulation dependencies.

After genuine responses arrive, score them against the frozen protocol, retain
negative findings, review the updated in-scope evidence and run required checks.
The owner-approved revised AE-011 engineering disposition permits a reviewed controller retry and successor recommendation; actual player validation remains deferred. Reconcile external config with durable state
using the controller's supported operator workflow; do not alter SQLite directly
or blindly rerun the initial manifest. Read [AGENTS.md](../AGENTS.md) and the
[controller handoff](campaigns/mvp/README.md) before starting a packet.

All delivery is local. `main` was not advanced and no remote push occurred.

## Remaining model and product limits

All outcome parameters and uncalibrated policy choices are conceptual/gameplay
assumptions. The experiments do not prove organizational or financial effects.
Evidence-coverage metrics are not Shannon entropy, semantic truth or calibrated
confidence. Actor-kind swaps do not change matched outcomes; replacement effects
must arise through future graph/functions/knowledge mechanisms.

The current prototype deliberately omits organizational replacement/functions,
incentive responses, live general snapshots, transport,
Godot UI, the 15–20 minute play loop, human enjoyment validation, save/resume,
packaging and MVP hardening. Mixed communication/delivery queue ownership and
some richer retry alternatives remain unresolved. These are campaign activities,
not implied by the accepted foundational tests. Continue risk reduction from the
actual gate; do not label this checkpoint the complete playable MVP.
