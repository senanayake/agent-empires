# AE-014 diagnostic ablation protocol

Saved before analysis. Question: does Impact × Uncertainty × Propagation ×
Persistence preserve useful distinctions beyond visible components and behavior?
This is an authored model challenge, not empirical calibration or a player study.

Units: uncertainty is an explicitly supplied unsupported-information fraction in
[0,1], not stated confidence, probability or automatically inferred truth. Impact
is conditional severity on a toy [0,1] scale, excluding traffic likelihood/count.
Propagation is distinct versioned downstream artifact IDs / a declared positive
artifact cap, saturated at one; repeated references never increase it. Persistence
is elapsed unsupported ticks / a positive age window, saturated at one (not a
rolling expiry). At creation it is zero. Resolution stops accumulated age, but
retains historical exposure; future evaluation cannot use a future resolution.
Reversibility is an authored fraction of consequences recoverable after reversal,
[0,1], kept visible separately. The optional modifier multiplies by (1-r); this
could misleadingly erase already incurred harm. No scalar enters damage rules.

Shared-source alternatives: sum per-assumption products versus maximum per
transitively overlapping declared source-root group, then sum groups. Exact
repeated assumption/version IDs count once; conflicting duplicates fail. Empty
root sets remain separate unknown groups. Group maxima are conservative bookkeeping,
not a bound on true joint risk; sources may share information but cause distinct harm.

Predeclared matrix: worlds A/B, seeds 0–15, arrival window 8 ticks; unsafe new-key,
safe stable-key, unsafe no-traffic, and unsafe zero-duplicate-exposure strategies.
Select decisions at tick zero, finish delivery, then advance the idle clock to
tick 16 before shipment. Scores use that pre-exposure snapshot; the newborn
gap is recorded at tick 16. This aging period is an authored control.
Each seed/world shares the same pre-sampled workload across strategies. Use current
PaymentCo input and existing paymentco_slice helpers, including their missing-info
records. All diagnostic metadata is authored separately; do not resample outcomes
for a formula. Save workload/rules/commands/history hashes and every run's metrics.
Duplicate charges >0 is the narrow diagnostic label; abandonment, cost and fitness
remain separate. Preserve incident-free unsafe seeds. Do not label debt as damage.

Authored counterexamples: maximum-debt ambiguous new-key harm, same-debt no traffic,
same-debt transient recovery, stable-key ambiguous protection, reversible low-impact
no-traffic choice, newborn zero-persistence ambiguous harm, and two different
component vectors with equal product. These challenge both prediction and explanation.

Ablations: no scalar keeps behavior, workload and outcome measures; its numerical
ranking baseline is a constant (all ties). Component vector preserves all five
values; its predeclared alert is I>=0.5 and U>=0.5 and P>0 and T>0. Scalar alerts use
cutoff 0.25. Report confusion counts and pairwise harmful/harmless concordance
(ties = 0.5), never calibrated probabilities or trained/test accuracy. Count mixed
harm labels at equal product versus equal vector, and product collisions losing
vector distinctions. Formula sweep: product; product × (1-r); geometric mean;
arithmetic mean; I×U (omit propagation/persistence). Sweep windows 4/16/64 ticks,
artifact caps 1/4/16, and product impact/uncertainty exponents 0.5/1/2. These are
invented MA-10 scale choices. Evaluate all choices against the same outcomes.

Falsifiers: a score changes authoritative history/outcomes; repeated propagation or
copied roots inflate the conservative aggregate; harmless debt is suppressed from
results; zero persistence hides immediate harm; scalar collisions conceal distinct
components. Recommendation: retain only as optional research diagnostic if it
preserves meaningful distinctions; change/remove if controls show misleading
prediction or lost explanations. No UI, punitive mechanism or architecture acceptance.

Artifacts: parameters.json, results.json, timing.json, recommendation.md, raw TDD
and validation receipts. Author CLI refuses existing results/timing, copies this
protocol before collecting. Verify CLI reruns into temporary storage, compares
canonical JSON and protocol/parameters, and checks fresh execution <=60 seconds
within the manifest's 300-second outer timeout. Timing bytes are not replay data.
Runtime CPython 3.12.13; locked uv environment. No failed seeds excluded. Scope
ledger lives in recommendation.md because shared campaign ledgers are out of scope.
