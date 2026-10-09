# AE-006 operator review

Disposition: accept the bounded mechanism after correcting evidence reuse.
This is a separate machine review by the root operator, not human participation
or empirical model validation. ADR-008 remains proposed.

Source, focused tests, authored traces and predecessor causal corrections were
reviewed. Two actual regression failures showed that revising a decision with
previously admitted evidence incorrectly weakened support, both with the original
holding and a copied holding after loss of original access. Those failures are
retained in `operator-evidence-red.json`. The correction preserves eligibility
only for the same immutable knowledge item, declared roots and assessment already
admitted for this decision. Current access and freshness are still required;
copied interpretation roots are still excluded. Reusing evidence adds zero new
source coverage. A stale copied holding remains weak.

`operator-evidence-green.json` records 41 focused / 168 total passing tests.
`operator-review-diff.json` contains the exact source/test correction. Original
worker output and receipt remain under `before-evidence-review/`; the worker's
38/165 counts and no-commit report are historical and were not rewritten.

The five authored traces were regenerated under model version
`ae006-decision-closure-v2-evidence-reuse`. Metrics, selected options and support
categories remain identical to the archived runs. Evidence eligibility metadata
now consistently preserves reused support. Repeated execution and fixed-profile
human/agent relabeling pass. These fixtures consume authored evidence; they do
not simulate payment outcomes or learning.

Limitations retained: declared evidence quality/source roots are trusted inputs,
not authenticated independence or semantic correctness. Coverage is not bits,
truth or calibrated uncertainty reduction. Authority delegation currently requires
live grant holders and live ancestors; that is an explicit toy policy to revisit
when organizational replacement becomes executable. No real participant,
comprehension, publication or full-MVP claim is made. Controller validation and
local delivery must still succeed before the next activity starts.
