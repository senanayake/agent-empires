# AE-004 review and scoped handoff

Reviewer: assigned AE-004 Codex worker, author self-review. Disposition: pass
for the bounded holdings mechanism; independent controller validation is pending.
No architecture/domain acceptance, human review or empirical calibration asserted.

## Predecessor and scope

Entry revision `5ac793d` contains AE-003's committed implementation despite its
historical worker staging failures. Reviewed actual clock/history/RNG code,
tests, replay runner/results, receipt, review and ADR-003/004/005, plus the required
campaign/domain documents. The receipt, 44 predecessor tests and full replay
verification passed before editing ([entry-checks.json](entry-checks.json)).
The retained within-stream RNG counterexample and lack of full reconstruction
do not block deterministic access rules. No architecture gate was inferred.

Updating MA-02/03 necessarily makes AE-003's assumptions input historical.
[Original bytes](predecessor-model-assumptions.md) match its entry hash; all other
predecessor bindings still match. The expected post-edit checker failure is kept
in [predecessor-binding-review.json](predecessor-binding-review.json). Its receipt
was not rewritten. Links in the archived document retain their original base.

## Mechanism and findings

The implementation applies the existing ADR-001/005/007 constraints. No new
architecture choice, dependency or ADR status is introduced; the ADR register
and shared handoff ledger are outside this packet's allowed paths.

| Claim | Reviewed evidence and limits |
| --- | --- |
| Identity-independent availability | One immutable Actor shape; no rule branches on name or kind. Tests compare human/agent traces, rename actors and move the sole holding. Actors have no implicit roles, grants or capability effects. |
| Items differ from holdings | Immutable item/version records are private catalog entries. Holdings separately carry owner, access, confidence, explicit freshness and source IDs. Registering a new item version neither publishes it nor replaces an older accessible version. |
| Genuine loss | Departure removes current personal access and artifact readership. `KnowledgeLost` marks a transition from some usable reader to none for an exact item/version. Catalog entries, artifacts and historical facts survive. A lost team gets `KnowledgeUnreachable`, including when organization access survives elsewhere. |
| Explicit reading | Actor holdings are personal; an artifact requires explicit content plus a named present reader. Team diagnostics union members' access; they never copy information to other members. All eight combinations of three holdings' access satisfy the union invariant. |
| No answer key | Only detached `ActorKnowledge` snapshots go to policies. Unknown, catalog-only, inaccessible and departed holdings yield no actor lookup result. Source IDs do not resolve hidden items. The trusted store and full audit must stay outside future actor/player interfaces. |
| Uncertainty retained | Stale high-confidence claims and a newer low-confidence alternative coexist. Syntactically different claims in the same authored topic flag conflict, without choosing truth. Three visible copies still yield one declared source, without raising confidence. |
| History and failures | Event payloads preserve item/holding snapshots. Access revisions append versions. Loss facts cite the removal event as direct cause; prior facts/views remain immutable. Bad parents, metadata, past time, duplicate/unknown/departed refs fail without state/history mutation. |
| Reproducibility | [Fixture](holdings.json) has two actors and one document. [Results](results.json), [history](history.json) and [manifest](run-manifest.json) repeat exactly, including reversed registration. The AE-003 clock orders departures at arbitrary ticks 3 and 6. No RNG is needed; these are structural controls, not statistical evidence. |

The fixture's negative findings matter: a surviving document becomes unreadable
when its last reader departs; copied policy is not independent evidence; high
confidence and freshness do not establish truth. No incident, actor penalty,
automatic transfer or global sharing was added to produce these findings.

## Validation and residual uncertainty

[Red](tdd-red.json) is the actual pre-implementation missing-module collection
failure (exit 2), not an invented assertion failure. [Initial green](tdd-green.json)
passed 37 tests. Boundary review added four tests plus a hidden-new-version
assertion; [final validation](worker-validation.json) passes 41 focused tests and
85 total tests. No production behavior fix was needed after initial green.
The initial run manifest is retained; strengthening test source changed its hash
only, while canonical history/results remained identical. Fixture verification
regenerates into temporary storage and never overwrites reviewed output.

Freshness uses explicit labels; no universal decay curve, observation quality,
truth, authority or belief update exists. Source IDs preserve declared dependence
but cannot certify source authenticity or independence. Access is direct reading,
not graph reachability; communication, costs, discovery, relearning and complete
replacement remain later packets. Re-enabling an artifact's access is permission
restoration, not empirical rediscovery. Old actor snapshots describe old access;
callers must refresh them after commands. In-process private attributes do not
isolate hostile Python code. No actor runner, UI projection, save/resume,
multi-owner transaction or threaded execution is proven here.

## Scoped activity ledger

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-004 | Holdings/access model, 41 tests, three-holder fixture, MA-02/03 and self-reviewed evidence prepared within allowed paths; commit blocked by read-only Git metadata. | Independent validation, delivery recovery and local integration remain controller-owned; no outcome asserted. |

Recommend AE-005 only after delivery and controller validation/review of this
packet. No successor was executed; no push or integration was attempted.

The single permitted staging attempt exited 128: Git could not create this
worktree's `index.lock` on its read-only metadata mount. [delivery.json](delivery.json)
preserves the exact error. No retry or worker commit is claimed. Source validation
is complete, but the required local commit needs controller/operator recovery;
the final worker delivery status is `failed` under the launch-specific policy.
