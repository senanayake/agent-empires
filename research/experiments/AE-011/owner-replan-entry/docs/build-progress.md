# Agent Empires build progress

Checkpoint: 2026-10-08 local date (2026-10-09 UTC), branch `build/mvp`.
This records local implementation and observed engineering results, not completion
of the playable MVP. Source of scope: [MVP campaign](mvp-campaign.md).

## Delivered and accepted

The campaign controller has accepted and locally integrated AE-001 through AE-010.
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

## Current AE-011 gate

Commit `4687ea8` integrates the reviewed trace renderer, 15 focused tests, neutral
phased reader materials, private audit traces, protocol and blank response template.
This was **operator partial local integration**, not a passing controller promotion.
The receipt remains `outcome: defer`, `participants: []`. The controller's original
failed attempt and blocked AE-011 queue remain unchanged. AE-012 and later work
have not been launched.

The controller independently passed focused tests and diff checking but failed the
required acceptance check. Its worker also could not create a Git index lock in
the protected shared metadata. The root operator reviewed and committed the
engineering preparation using its available local Git permissions. Recovering
delivery does not satisfy the missing human evidence. See
[operator review](../research/experiments/AE-011/operator-review.md) and the
[original delivery failure](../research/experiments/AE-011/delivery.json).

Collect three distinct actual unfamiliar, consented readers using only the final
[reader materials](../research/experiments/AE-011/packet/reader/instructions.md).
The facilitator uses the private
[protocol](../research/experiments/AE-011/protocol.md) and
[response template](../research/experiments/AE-011/response-template.md).
Keep raw anonymized answers, familiarity screening, material hashes, prompts,
confusion and dissent. Do not show the facilitator rubric or audit to readers
before their primary responses are frozen. No invitation has been sent and no
response or participant identity has been invented.

The criterion remains at least two of three identifying an unsupported choice
and proposing a plausible intervention without thesis priming. This is an invented
formative design threshold, not statistical evidence. Missing responses defer
acceptance; a negative readback requires a bounded revision. Both block dependent
work. The supplied histories test inference, delivery and delayed observation;
they do not yet contain the Sarah-replacement story.

## Reproduce this checkpoint

Use the pinned CPython 3.12.13 and locked project environment, separate from the
controller environment:

```bash
uv sync --locked --python 3.12.13 --group dev
uv run --locked --python 3.12.13 --group dev python3 -m pytest -q
uv run --locked --python 3.12.13 --group dev python3 experiments/paymentco_slice.py --verify-against research/experiments/AE-010
uv run --locked --python 3.12.13 --group dev python3 experiments/trace_report.py --verify-against research/experiments/AE-011/packet
uv run --locked --python 3.12.13 --group dev python3 scripts/check_campaign.py
uv run --locked --python 3.12.13 --group dev python3 scripts/check_campaign.py --activity AE-010
```

The last independent engineering run passed **312 tests**, regenerated the reader
packet byte for byte, and reproduced all **357** paired/boundary PaymentCo cases
and canonical traces. Raw command results are in
[operator-checks.json](../research/experiments/AE-011/operator-checks.json).
Running `scripts/check_campaign.py --activity AE-011` must currently exit 1:
`gate is not pass`. Do not change the checker or declare a pass to proceed.

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
- Active blocked attempt: `AE-011-20261009T022454Z`.
- Clean integration target: `/home/senanayake/Dev/agent-empires-mvp-integration`,
  branch `build/mvp-integration`, then fast-forwarded to this `build/mvp` checkout.

The clean target preserves the user's untracked `img/AgentEmpires.png` in the
original checkout; that image was not staged or modified. The committed campaign
manifest retains its initial statuses, and launch-time YAML can also predate the
last state transition. The durable database records AE-001–010 complete, AE-011
blocked and AE-012–035 pending. Neither the baseline manifest nor a worker commit
is a current acceptance ledger.

Earlier workers hit the same protected Git metadata limitation. Original attempts
and failures were preserved, then reviewed artifacts received bounded delivery
retries and actual controller validation/promotion. Local operator review records
and retry helpers are under `/home/senanayake/.local/state/agent-empires-mvp/`.
They are host-specific orchestration aids, not simulation dependencies.

After genuine responses arrive, score them against the frozen protocol, retain
negative findings, review the updated in-scope evidence and run required checks.
Only a passing substantive AE-011 disposition permits a reviewed controller
retry and successor recommendation. Reconcile external config with durable state
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

The current prototype deliberately omits full learning loops, organizational
replacement/functions, incentive responses, live general snapshots, transport,
Godot UI, the 15–20 minute play loop, human enjoyment validation, save/resume,
packaging and MVP hardening. Mixed communication/delivery queue ownership and
some richer retry alternatives remain unresolved. These are campaign activities,
not implied by the accepted foundational tests. Continue risk reduction from the
actual gate; do not label this checkpoint the complete playable MVP.
