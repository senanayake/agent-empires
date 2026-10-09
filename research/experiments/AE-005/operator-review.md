# AE-005 operator causal review

The root Codex operator reviewed the source and added three independent regression
tests. All three failed against the worker implementation: forwarding lost the
distortion event from its ancestry, restored access lost the original acquisition,
and recipient-unavailable loss did not cite departure. Raw failures are retained
in `operator-causal-red.json`; the correction is in `operator-causal-fix.json`.

A send now cites both the completed acquisition and current access fact, plus
the connection. Acquisition uses `KnowledgeTransferred` when present because it
includes distortion evidence; `KnowledgeHoldingRecorded` alone is a storage fact.
Access restoration cannot replace that origin. Unavailable-recipient loss cites
the actual departure. Future decision/trace consumers must preserve this distinction.

After correction, 42 channel tests and all 127 tests pass. The unchanged protocol
was rerun across 160 seeded cases and four topologies under model revision
`ae005-one-hop-v2-causal-ancestry`. Results are byte-identical; only the representative
chain trace changes to retain transfer ancestry. Prior outputs and the original
worker receipt remain in `before-causal-review/`; historical 39/124-test receipts
are not current validation of this revision.

This is machine code review and toy-model evidence, not empirical calibration,
human comprehension or independent organizational research. Capacity rejects
excess admissions rather than buffering; departure is observed through the shared
history, and actor kind never changes channel outcomes. Full reconstruction and
player-facing access restrictions remain later activities.
