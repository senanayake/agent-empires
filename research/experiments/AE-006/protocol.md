# AE-006 bounded transition protocol

Worker self-review; no participants or calibrated parameters. Review entry AE-005
source, receipt, corrected causal review and replay before edits. Entry checks
pass (42 tests and 160 cases/four topologies); historical Git failures are followed
by committed artifacts in this checkout. No architecture acceptance is inferred.

Implement ADR-008's proposed immutable decision versions and separate grant owner
within the two allowed simulation modules. Profiles use deterministic preference,
claim-reading capability and stated categorical confidence; no accuracy oracle or
new RNG is needed. Only current actor holdings can supply rationale/evidence.
Authority has exact action/scope/option, half-open validity and revocable delegation
ancestry. Trusted setup imports root grants; runtime delegation cannot widen them.

Before implementation, execute tests for the five AE-002 decision slices: T1
inferred/green verification then delivered independent challenge; T2 delegated
without learning then revoked; T3 authorized policy challenged by an authored
observation and revised; T4 shared reports plus conflicting independent evidence;
T5 benign, non-discriminating observation without authority. Outcome/assurance/
belief engines remain AE-009/010/013 work: observations are explicitly authored
holdings, not simulated payment results or measured fitness.

Falsifiers: closure/grants add world evidence; inaccessible evidence is consumed;
old versions change; copies gain support; stale/revoked grants pass; actor labels
change matched-profile traces; unsupported confidence cannot be high. Negative,
boundary, stale-version and rejection-without-mutation tests accompany the cases.
Evidence methods, quality and source roots are declared trusted metadata; unique
labels cannot establish authentic independence. Metric units are distinct usable
source roots consumed per question, not bits/probabilities or truth. Conflicting
and inconclusive observations can add source coverage without resolving a choice.

Generate closure-trace.json from an executable deterministic fixture, include all
five cases and full histories, and verify by regeneration without overwriting.
Controls: repeat, actor-kind relabeling with fixed profiles and holdings. Seed is
null for decision policy; communication integration uses fixed seed 7 with loss
0 and latency 1 tick (invented boundary controls, not calibration). Preserve all
actual red results and any failed probes. Run required validations and the full
existing suite once green. Review limits before binding final receipt hashes.
