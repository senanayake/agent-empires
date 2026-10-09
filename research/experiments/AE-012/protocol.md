# AE-012 paired clarification protocol

Saved before collection/analysis. Scope: [AE-012](../../../docs/mvp-campaign.md#ae-012--compare-clarification-with-silent-inference).
Parameters and budgets are predeclared in `protocol.json`; all are invented.

Compare Story → Actor with Story → Clarification → Actor in the same PaymentCo
initial state, world, immutable workload and seed. Fix five retry choices to
all failures, three retries, fixed backoff, all declines and attempt lineage.
For idempotency use the same exact-claim actor policy in both arms: prefer new
keys, stable keys, unspecified. The wrong-answer condition instead starts both
arms with stable-key preference, then supplies a mistaken new-key claim. This
allows asking to worsen a previously harmless inference rather than making all
wrong answers redundant. Actor kind is held fixed; a matched-kind control tests
that relabeling alone changes no history.

Ask Ada over explicit Jin→Ada and Ada→Jin channels. Helpful/out-of-scope/lossy/
harmless use Ada's existing stable-key holding. Unavailable means no service
availability before the timeout. Wrong replaces only Ada's accessible exact
claim with new-key content, preserving its declared source. Conflicting adds
that alternative without removing the original. Stale replaces the accessible
holding with a stale copy. Out-of-scope cites an unrelated existing grant; it
must retain sources without legitimate answer authority. Harmless sets hidden
commit exposure to zero in both arms, leaving the same workload draws untouched.
All runtime changes, channel parameters and ordered commands are recorded.

Request and response latency, earliest availability and service ticks delay
work. Requests reject capacity congestion. Finite answer batches reserve one
channel slot per claim and may time out with partial holdings. Loss is seeded
separately from world draws. The holder view is refreshed at response time;
accepted answer batches snapshot holdings then, like AE-005 transfer admission.
Copies retain source roots. Stale answers are audited but not used by this
clarification policy. Conflict uses preference order without majority voting.
Holder authority at receipt remains separate from requester authority; none of
these reports automatically produces independent evidence or a validated belief.

Run 16 seeds × two worlds × eight answer conditions × two timing profiles, with
two arms each (1,024 trajectories). Preserve all paired duplicate, abandonment,
retry resource, shipping time and channel cost differences, including losses,
ties, reversals and incident-free inference seeds. Keep seed-zero full causal
histories and all history hashes. Record each workload once with its hash; both
arms must bind that same hash. Physical arrivals remain relative to ship, as in
AE-010; absolute shipping/terminal times therefore expose the waiting difference.

Report no single universal utility. For every pair, compute the change in
modeled cost: duplicate count × declared duplicate penalty + retry resources +
work resources + channel resources + shipping tick × declared delay cost per
tick. The 3 × 3 sensitivity grid exposes when benefit exceeds expense. This is
an invented opportunity-cost proxy, not observed payments/customer harm. Report
mean/min/max and winning/tied/losing seeds for every condition/profile/grid cell.

Falsifiers: mismatched world samples; actor-kind-only effects; stale claims
changing the option; holder authority silently granting requester authority;
copies becoming independent evidence; clarification winning every harmless
positive-delay comparison. Helpful answers need not win with low exposure or
high waiting cost. Wrong/conflicting/unavailable answers must remain visible.

Author with `--output-dir` only in fresh evidence storage; save the exact protocol
before collecting. Verify with `--verify-against` in temporary storage, comparing
canonical results and traces without modifying evidence. Check fresh full-run
wall time ≤ 120 seconds (engineering budget inside the manifest's 300 seconds;
not a gameplay or universal performance claim). Reject modified protocols/results
and existing authored output. CPython 3.12.13 and locked checkout dependencies.
Reviewer will be the assigned worker's self-review; independent controller checks
and unfamiliar-player evidence remain external/later. No new ADR is needed for
this bounded operation under the existing time/provenance/import constraints.
