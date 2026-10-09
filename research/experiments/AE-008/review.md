# AE-008 review and scoped ledger

Disposition: **pass for the bounded scenario-input contract**. Reviewer: assigned
AE-008 Codex worker self-review; no independent domain or human reviewer. JSON
was selected under the packet's explicit alternative to YAML; no mechanism,
manifest, checker, simulation owner or dependency was changed.

## Predecessor and entry review

Entry branch was `campaign/agent-empires-mvp/AE-008/AE-008-20261009T010018Z`,
clean at `4d33f2a`. AE-007's artifacts and receipt are committed here despite its
historical no-commit worker limitation. Its entry receipt check passed. Reviewed
its protocol, decision/gate review, recorded results, actual simulation interfaces
and composition source. `predecessor-summary.json` extracts all 18 case summaries
across seeds 7/19/31: no failed seeds/controls; loss versus surviving transfer,
closure without evidence, delegation without evidence and challenged authorized
policy remain distinct. `predecessor-replay.json` records a fresh canonical replay
pass without overwriting predecessor artifacts. Three zero-loss/distortion seeds
are not calibration or distributional evidence; authored observations are not
payment outcomes. No contradiction prevents this authoring scope.

AE-008 legitimately updates the predecessor-bound ADR register and scenario brief.
Their exact entry copies are preserved as `entry-adr-README.md` and
`entry-paymentco-README.md`. The AE-007 receipt remains historical after those
shared documentation changes; it was neither rewritten nor falsely represented
as a current unchanged hash pass. The checked source, tests, lock and experiment
remain unchanged. This receipt records entry predecessor acceptance separately
from the current AE-008 input hashes.

## Delivered behavior and substantive checks

`scenario.json` contains ten human actors, one human and three optional agent
capability profiles, six decisions, scoped root grants, two initial policies,
explicit claims/holdings, private informal functions, nine directed channels and
two worlds. Numeric operating inputs use the register's provenance fields,
checked units, admissible and sensitivity ranges. All are invented toy parameters
with null calibration versions. An unused/tacit claim need not have a holder;
retention is not access. A document with no readers remains unreadable.

The loader rejects duplicate JSON keys and typed IDs, invalid/missing references,
incompatible versions, impossible alternatives, unauthorized policy actor/scope/
option references, unknown sources, wrong units, malformed probabilities,
nonfinite/bool numbers, range violations and unimplemented schema keywords.
Exact-byte SHA-256 is checked against an optional expected manifest hash. UTF-8
JSON is required; YAML tags cannot execute. World mixes normalize to one, and
zero workload and probability boundaries are legal.

Existing AE-004 knowledge ownership and AE-006 policy APIs are reused. Loading
registers items without sharing them, records only authored tick-0 holdings,
and never performs inference, message delivery or world sampling. Profiles rank
exactly each question's alternatives. All four profiles can propose through the
same API; actor-kind relabeling grants no extra knowledge. Changing/reordering
private worlds leaves every actor snapshot identical. The independently authored
Jin snapshot contains the thin work item, formal roster, alternatives, public
goal values and repository holding; it omits Sarah's historical claim, inaccessible
archive and all private catalogs/parameters/functions. Explicit artifact access
and a fresh simulation store's post-departure access were checked separately.
Returned snapshots and audit copies cannot mutate initial owner state.

## Actual red/green evidence

- `tdd-red.json`: real collection failure before implementation (missing loader).
- `first-implementation.json`: 29 focused tests passed after the first loader/data.
- `review-red.json`: 3 failures / 40 passes. UTF-16 and scenario version 2.0.0
  were incorrectly accepted, and public goal parameter values were missing.
- `review-green.json`: those repairs passed all 43 tests; the snapshot fixture
  was explicitly extended with public goal parameters, not private world data.
- `numeric-red.json`: 1 failure / 44 passes. Oversized integer raised an incidental
  float-conversion OverflowError. Integer finiteness handling was corrected;
  admissible range rejection now produces ScenarioError.
- `focused-tests.json`: final 45 focused tests pass.
- `full-suite.json`: all 232 existing/new tests pass on CPython 3.12.13 with
  pytest 9.1.1 in this checkout's uv-locked environment.

Negative outputs remain unedited. No seeded payment experiment or participant
study was performed. These tests establish authored structure and modeled access,
not schema certification, scientific validity, or a successful payment policy.

## Limits and delivery ledger

The standard-library validator implements only the bundled schema vocabulary;
it is not a general Draft 2020-12 implementation. Schema/data lookup currently
assumes the source checkout; packaged resource handling is AE-032. Python API
projections do not protect against introspection/malicious authors. Authored
source/authority metadata are trusted; semantic truth and real legitimacy are not
verified. Initial snapshots are not live runtime permissions. Speed/cost,
availability, adaptive retry, functions, communication setup and policy enactment
remain inputs for later owners/services. Payment exposure/outcome/learning rules,
empirical calibration and all human comprehension/engagement claims remain absent.

| Activity | Repository disposition | Controller disposition |
| --- | --- | --- |
| AE-008 | JSON/schema/loader, negative and access tests, ADR-010/model guide, self-review and bound receipt complete. Local delivery is reported by the worker; any failed attempt is preserved in delivery.json. | Independent validation, commit recovery if needed and local integration belong to the controller; no integration/publication or campaign-completion assertion. |

Shared handoff ledger is outside the allowed paths; this is the scoped update.
AE-009 is the bounded successor only after actual local delivery and controller
validation/review. This worker does not execute it, push or alter controller state.

The single permitted staging attempt returned exit 128 because Git could not
create the shared worktree `index.lock` on a read-only filesystem. No commit was
attempted after staging failed, and no retry or push occurred. `delivery.json`
preserves the exact command/error. Implementation and repository validation pass;
required local delivery remains failed. The worker therefore recommends no
successor until controller/operator hash-reviewed commit recovery and independent
validation. This is not a failed domain hypothesis or permission to weaken gates.

## Subsequent operator review

The original worker account remains above. [operator-review.md](operator-review.md)
records a schema-reference assertion regression and correction, with 46 focused
and 233 total tests passing. Authored scenario data and snapshots are unchanged.
