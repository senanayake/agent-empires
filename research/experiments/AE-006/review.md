# AE-006 review and scoped handoff

Disposition: pass for the bounded mechanism, by the assigned AE-006 Codex worker
(self-review). No independent reviewer, human participant, calibrated model or
architecture acceptance is implied. ADR-008 remains proposed; this implements its
existing hypothesis without a new architecture decision. Shared ADR/ledger files
are outside the allowed paths, so the activity ledger is recorded here.

## Predecessor and boundaries

Reviewed actual AE-005 channel/holding/history code, tests, receipt, corrected
operator causal review, source-bound experiment manifest and all-seed results.
The predecessor receipt, 42 focused tests and 160-case/four-topology replay passed
at entry. Historical worker delivery failures were followed by committed artifacts
present here; no controller integration claim is inferred from those artifacts.

MA-01/02/05/06/09 now describe this activity. That permitted successor edit makes
AE-005's shared assumptions binding historical. The original bytes are archived
in `predecessor-model-assumptions.md`; `predecessor-binding-review.json` verifies
an exact match and every other predecessor binding remains current. The actual
post-edit checker failure is retained in `worker-validation.json`. No predecessor
receipt, manifest or checker was changed.

## Findings

Decisions append immutable versions; stale commands, invalid choices, unavailable
holdings and invalid authority fail before publishing state/history. Authority is
owned separately: root import/revocation are trusted organizational inputs, while
delegation must narrow a valid parent. Scope, action, actor, options, expiry and
revoked ancestors are checked again for each claimed authorized action. Expiry is
half-open. Historical grant evaluations survive revocation; deliberate unsupported
selection is a separate path, with an AssumptionMade event and known missing inputs.

Both actor kinds use the same capability profile. Inference reads only current
accessible claims, ranks options by declared preference, and does not count copies
as votes. Claim reading and inference can be disabled. Confidence stays categorical
and stated, including high confidence with no support or conflicting evidence.
Acquisition and current access are separate causal parents: transferred distortion
remains traceable after access is revoked and restored.

Evidence assessments pin a question or prior decision, accessible item/holding
versions, stance, method and quality. Ultimate source roots come from holdings.
Verification is not fitness evidence. Shared subject roots, stale/unknown freshness,
weak quality and missing roots cannot add evidence coverage. Revisions retain old
source dependencies; question-level citations cannot bypass existing choice lineage.
Contradictory claims remain visible even after a precautionary change of option.

`evidence_backed_information_gain` measures distinct (question, usable declared
root) pairs consumed, **not** entropy, independent samples, truth, calibrated
probabilities or belief revision. Conflicting and inconclusive observations can
increase this coverage. Inference/delegation add zero; repeated copies add zero.
Metrics are privileged audit diagnostics, not player-visible knowledge snapshots.

| AE-002 decision slice | Executed result | Evidence coverage at end |
| --- | --- | --- |
| T1 inferred/green | Closure and high confidence without evidence; copied verification remains weak; independent observation permits an explicit precaution under a grant | 1 root |
| T2 delegated | Grant and closure add no evidence; scope/revocation rejections preserve state; unsupported revision leaves prior authority intact | 0 roots |
| T3 wrong authorized policy | Authored observation challenges authorized choice; changing authorization is a separate input; old version stays pinned | 1 root |
| T4 shared/conflicting | Two reports share one source; independent challenge retains conflict through a cautious revision | 2 roots |
| T5 benign unsupported | Authored limited benign window adds coverage without distinguishing caps or supplying authority | 1 root |

All cases close one decision; revisions never increase closure count. T1 does not
prove stable-key correctness; T3 does not implement trial deployment or policy
learning; T5 does not simulate a no-harm outcome. These are the decision slices
of the five tabletop cases, with explicit authored evidence inputs. World outcomes,
assurance execution and learning remain AE-009/010/013, not fabricated results.

## Validation and negative results

`tdd-red.json` records the actual missing-module collection failure. The initial
implementation passed 33 tests. Review added two regression probes that actually
failed: a generic question citation laundered a copied interpretation, and a
revision dropped the original dependency. `provenance-red.json` retains 2 failures /
36 passes; `provenance-green.json` records the repaired 38-pass suite. Original
failures were not overwritten. No statistical or random inference rule was added.

Final worker checks: 38 decision tests and all 165 tests pass. The authored fixture
regenerates five histories byte-for-byte and passes fixed-profile actor relabeling.
Its manifest binds code, fixture, protocol, runtime and lockfile. Decision seed is
null because this policy is deterministic. The channel composition test uses seed
7, loss 0 and latency 1 as invented boundary controls, preserving distortion ancestry.
Actual raw commands/results are in `worker-validation.json` and acceptance checks.

Limits: declared source identities/quality/assessments are trusted, not authenticated
or semantically inferred. Distinct roots can still be correlated. Selection-history
lineage is conservatively cumulative and may exclude otherwise useful future
support; exact historical subjects preserve observation context. Questions cannot
change scope/alternatives in place. Multiple conflicting organizational policies,
permission-notice beliefs, concurrent owners, persistence and reconstruction are
not implemented. Same store/history and trusted single ownership remain caller
contracts. No actual participants, empirical calibration, product comprehension,
integration, publication or full PaymentCo scenario evidence is supplied.

## Scoped ledger

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-006 | Decision/authority/evidence mechanism, 38 tests, reproducible five-case trace, assumptions update and worker self-review complete. Local delivery failed: shared Git metadata is read-only; no worker commit exists. | Independent validation and local integration remain controller-owned; no campaign-completion decision. |

AE-007 is the bounded successor only after delivery and controller validation.
It was not launched or implemented here. Push remains disabled.

## Local delivery limitation

The single permitted `git add` attempt failed with exit 128 because Git could not
create the shared worktree `index.lock`: read-only file system. `delivery.json`
retains the exact command and error. No commit, retry or push was attempted. The
completed source and passing tests remain for controller/operator delivery recovery.
Launch policy requires the final worker status to be `failed` for this required
delivery blocker. No successor is recommended until local delivery is recovered.

## Subsequent operator review

The original worker record above is retained. See [operator-review.md](operator-review.md)
for two additional failing regressions, the evidence-reuse correction, 41/168
passing tests, and the versioned regenerated traces. Local delivery is separate.
