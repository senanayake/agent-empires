# AE-020 worker review and handoff ledger

Reviewer: assigned Codex worker, **self-review**. Disposition: source/docs ready for
controller-owned independent validation under the packet's runtime semantics.
No independent architecture/domain/human review is implied.

Reviewed AE-016's actual live lifecycle source, seven traces/16 paired seeds,
protocol, worker review, root compatibility review and assembled-target validation.
The current entry predecessor checker passed. Loss seeds, cancellation with paid
costs, incomplete function/capability equivalence, no incident exposure and absent
player evidence remain limitations. The original local worker delivery error was
resolved upstream in the root-reviewed assembled predecessor; this checkout
contains that source/evidence at entry HEAD recorded in environment.json.

AE-020 changes the shared ADR register legitimately. Its entry bytes and unchanged
AE-016 receipt are archived in entry/ before this change; the entry predecessor
check is preserved. Predecessor inputs that referenced that register are historical
after this successor edit, not rewritten or silently rebound. No scenario/domain
source, manifest, checker, controller state or shared build ledger is changed.

Commands are a passive preview only: strict version/run/IDs/args, exact retry
acknowledgments, bounded ID cache, pause/explicit dispatch and public detached state.
HTTP framing is separate from application orchestration. The server binds only
loopback and serializes access to one state owner. Startup calls real Jin delivery;
reconnect includes immutable verification dimensions and current live roster.
No management action or public/cloud/auth/LLM platform is introduced. Application
projections omit private holdings/functions/world/lineage. Unknown facts redact by
default while retaining contiguous event IDs/cursors. Rich causal inspection is
future scope, not silently exposed through event payloads.

Actual TDD failures are preserved as JSON strings: missing command module (red.json),
socket-denied first run plus omitted existing fractions import (first-green.json),
wrong proposal timestamp (handler-green-attempt.json), and missing reconnect
assessments (reconnect-red.json). Corrections yield 33 passing socket-free handler,
application, redaction, duplicate/disconnect, negative framing, batch invariant,
live replacement, seeded domain-equivalence and import-boundary tests. The final
required focused command retains 33 passes/one kernel-socket PermissionError;
there is no full focused-suite pass claim. The real loopback test remains enabled
for controller validation. No socket test is converted into a skip or mock pass.

Benchmark protocol is encoded before measurement in benchmark.py: one real work
completion, 30 warmups, 300 mixed serial requests, seed 0, new connection per
request and nearest-rank p95. measurement.json records the actual separate-process
loopback failure and hardware. Handler-only diagnostic p95 0.403191 ms excludes
kernel sockets/process scheduling, so **the under-250-ms loopback budget is
unproven**. No second adapter is benchmarked: sandbox access is not evidence that
HTTP fails its transport criteria. Selection remains provisional; the root/controller
can run benchmark.py into a fresh external output path on an authorized runtime.
Neither benchmark output nor test code may overwrite this negative evidence.

Residual limits: 4,096 cached IDs/process, in-memory history/cache, no process-loss
restore, two-second sequential slow-reader timeout, small preview workload, AST
import checks rather than arbitrary dynamic-code enforcement, no packaged launcher,
Godot client/frame-independent replay or player study. AE-017/018/019 remain
unpassed gates before controls. ADR-011 records an existing product constraint,
not complete offline packaging evidence.

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-020 | Application protocol, one HTTP adapter, public preview contract, focused tests, benchmark and preserved failures, ADR-009/011 and current hashed self-review receipt. Local Git delivery recorded separately if it fails. | Real loopback tests/budget, independent acceptance and local integration remain controller-owned. No publication or campaign completion claimed. |

The controller should validate the unchanged live socket test and collect a real
loopback measurement before accepting the transport budget and handing off AE-021.
This worker does not execute that successor or integrate/push any branch.

Final local delivery: the single permitted `git add` attempt failed with exit 128
because shared worktree Git metadata could not create index.lock on a read-only
filesystem. delivery.json retains the exact command/error. No commit, retry, push
or integration occurred. The final worker status is failed for required local
delivery despite completed source/docs. Root/operator hash-reviewed delivery
recovery and independent live socket/budget validation remain required. No
successor is recommended by this failed-delivery attempt.

Optional unchanged-domain regression: **487 passed in 49.99 seconds**. Final
required receipt and tracked diff checks pass; the required full focused test
remains 33 passed/one sandbox socket error. No acceptance gate is weakened.
