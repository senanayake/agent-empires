# AE-003 review and scoped handoff

Reviewer: assigned AE-003 Codex worker, author self-review, 2026-10-08.
Disposition: pass for this engineering packet; no independent domain/architecture
review, participants, target integration or publication asserted.

## Entry and predecessor review

Entry HEAD: `4a0d639`; clean assigned branch. Read campaign sections 2–8/AE-003,
manifest, assumptions, PaymentCo brief, ADR register/template and handoff. AE-002
is the sole predecessor and its current receipt passed before edits under
CPython 3.12.13; [entry-checks.json](entry-checks.json) preserves output and hashes.
The missing initial AE-003 receipt failed, as recorded, and is not a behavior test.

Reviewed AE-002's actual language/domain/context documents, ADR-006/007/008,
five tabletop traces, review, validation and operator-recovery record. T2 requires
permission to remain distinct from evidence; T3 preserves old deployed subjects;
T4 distinguishes source support/association from modeled direct cause and requires
explicit delivery; T5 rejects automatic assumption penalties. Those findings
support immutable version refs and typed earlier parents, without implementing
decision rules here. Cross-owner atomicity, source independence and save/replay
were expressly unresolved; no missing or contradictory prerequisite was found.
AE-002 recovery was operator-reviewed and delivered in this checkout; the worker's
original interruption remains visible. No independent domain acceptance follows.

Required AE-003 updates to `docs/adr/README.md` and `docs/development.md` make
those two AE-002 bindings historical. Exact pre-edit bytes are archived as
[predecessor-adr-register.md](predecessor-adr-register.md) and
[predecessor-development.md](predecessor-development.md); links in those snapshots
retain their original document bases. All other predecessor inputs/artifacts stay
unchanged. AE-002's receipt is preserved, not rewritten to bless this implementation.

## Implementation review

| Claim | Review and bounded evidence |
| --- | --- |
| Explicit time/order | Queue key is tick/priority/insertion sequence; tests include reverse lexical IDs, same-tick dynamic insertions, 150 scheduled ties, idle advancement and rejected past/skipped ticks. Priority affects only pending work. |
| Atomic negative cases | Scheduling validation precedes sequence allocation; history validates parents/schema/payload before append. Failed commands consume no IDs. Bool/fractional time, invalid metadata, dangling/self/future/foreign parents and cyclic payloads fail. |
| Immutable history | Frozen envelopes/refs, tuple snapshots and immutable payload bytes prevent caller and nested exported-data mutations from changing canonical history. The private Python attributes are not a hostile-code security boundary. |
| Causal DAG | Parents must already exist in the same history; all links in the 40-fact graph point to lower sequences. Relation labels distinguish direct cause, evidence and association; they do not prove actual causality. |
| Canonical bytes | Nested map order does not matter; arrays retain explicit order; UTF-8 JSON uses ASCII escapes, sorted keys, finite numbers and no whitespace. Exact stored seed histories are checked, not just parsed structures. |
| Named RNG | SHA-256 derivation avoids process hash randomization. Extra actor-stream draws leave world samples unchanged. Same-stream extra draws shift samples; that counterexample is retained in results, not treated as a solved counterfactual problem. |
| Replay envelope | Seeds 17/23, repeat, split advancement, unrelated draws and both fresh-process hash seeds (1/987) reproduce. Time/ambient RNG/entropy calls are forbidden during the unit replay. Manifest binds exact source, fixture, lock, runtime and ordering. |
| Dependency direction | Manually inspected simulation imports: dataclasses, heapq, json, hashlib, random and internal clock only. There is no application, adapter, UI, transport or service import. Comprehensive future architecture gates are not claimed. |

## Actual tests and retained failures

[tdd-red.json](tdd-red.json) records the focused command exiting 2 because the
new clock/events modules were absent before implementation. This is missing-API
red, not an assertion failure in a pre-existing behavior. After implementation
the same focused command passed **44 tests**, recorded in
[tdd-green.json](tdd-green.json). Final validation strengthens fresh-process
coverage to both seeds. No simulated or inferred red output is substituted.

Initial network locking failed on DNS; [bootstrap-lock.txt](bootstrap-lock.txt)
retains raw output. A first cache-copy attempt expected pytest metadata in v22,
but it was in v21; the final [setup record](bootstrap-offline.json) explains the
correction. Offline uv locking and locked sync then succeeded with copied cached
packages, a local ignored `.venv`, setuptools 82.0.1 and pytest 9.1.1. The hardlink
warning fell back to successful copies. No alternate-runtime or controller-venv
validation was used. Setup failure is preserved and resolved, not a remaining gate.

The protocol was written before implementation/results. All tested seeds are
retained; none failed the engineering controls. There are no tuned outcome rates,
participant records, payment rules or empirical claims. Frozen JSON event data
and four commands do not establish full reconstruction, state restore,
cross-runtime portability, thread safety, performance/queue budgets, statistical
independence, aligned endogenous counterfactual samples or player comprehension.

## Activity ledger within allowed scope

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-003 | Clock, named RNG, immutable causal history, locked package, 44 tests, command fixture/run manifest and ADR-003/004/005 delivered with self-reviewed evidence. | Independent required validations and any local integration remain controller-owned; no outcome asserted here. |

The shared handoff ledger is outside exact allowed paths, so this entry is the
scoped handoff. Recommend **AE-004** only after controller validation/delivery and
review of these artifacts. Do not execute it. Commit locally; push is disabled.

Worker delivery limitation: both actual staging attempts returned exit 128 because
the worktree Git index is on a read-only mount. [delivery.json](delivery.json)
retains the error; no local commit or push exists. Required worker validations
passed, and edits are complete for independent controller validation. Controller
or operator recovery must commit the reviewed files with writable Git metadata.
The empty-index staged diff command is not evidence of staged content; a separate
new-file whitespace check covers the untracked files.
