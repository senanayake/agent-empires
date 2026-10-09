# AE-012 independent operator review

Reviewer: root operator, separately from the controller-launched worker.
Disposition: accept the bounded mechanism and toy comparison after reviewed local
delivery. No implementation correction was needed after final worker self-review.

Read the learning owner, focused tests, paired harness, protocol, raw controls and
worker findings. Clarification requires directed request/response paths, costs
time/resources, reads only accessible holder claims at response, and preserves
source roots and current access ancestry. Accepted response batches snapshot at
service time, explicitly matching admission semantics rather than continuous
sender access. Receiver departure prevents acquisition. Monotonic task IDs avoid
batch collisions, and timeout priority preserves exact-deadline partial replies.

Independent spot checks confirmed truncated deadline replies remain in the result
and knowledge view, and different rejected authority claims remain distinguishable
in history. Holder rights at receipt do not authorize the requester or validate
the claim. Wrong/current claims can change behavior; stale claims remain recorded
but do not influence this clarification policy. Evidence coverage is not invented.

The paired harness uses the same immutable world workload and initial state in
both arms. Its delay-cost grid is an explicit invented opportunity-cost measure,
separate from physical outcomes. It retains harmful misinformation, harmless
inference, incident-free seeds, ties and reversals; it does not make asking
universally optimal. The initial and final 512 pairs are compared in
`operator-checks.json`: the authority-audit correction changes history hashes,
while numerical trajectories and sensitivity analyses remain unchanged.

Independent checks cover all 339 project tests, replay of all 1,024 trajectories,
current receipt integrity and diff checking. The worker's earlier 336-test result
predates its final three tests; the actual final suite includes them. Original
negative tests, initial run and protected-Git failure are preserved. The root
will use a fresh controller-owned, hash-pinned delivery retry; that retry's
validation/promotion is separate from this review. No remote push is authorized.

The MA-09 document update legitimately makes earlier model-register bindings
historical; the exact predecessor receipt and register at entry are retained.
Do not rewrite prior acceptance to imply later checks were run earlier.

Limits remain: authored availability without a shared actor queue; finite exact
claims and syntactic conflict; uncalibrated cost weights; arrivals relative to
deployment; no conversational LLM, general belief learning, UI or actual player
study. Owner-directed development feedback is distinct from unfamiliar-player
evidence at AE-029. Recommend AE-013 after actual reviewed integration.
