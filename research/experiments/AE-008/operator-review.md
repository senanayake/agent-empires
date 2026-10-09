# AE-008 operator review

Disposition: accept the bounded input contract after a schema-reference fix.
The root operator separately read the loader, all tests, ADR, model contract,
scenario roster/holdings/grants/decisions/profiles/worlds, and worker review.
This is machine review, with no participant or empirical calibration claim.

A supported assertion beside a local `$ref` was silently skipped. An actual
failing regression is retained in `operator-schema-red.json` (1 failed / 45
passed). Following a reference now checks the referenced rule and its siblings.
`operator-schema-green.json` records 46 focused / 233 total passing tests.
The exact correction is retained in `operator-review-diff.json`. Authored data,
file identity and initial access projections are unchanged. Original worker
receipt and its 45/232 test statements remain historical, not rewritten evidence.

Typed reference checks, strict numeric units/bounds, version/byte identity and
personal/readable-artifact access are coherent. The world-change control keeps
private rates out of actor snapshots; actor kind grants no knowledge. Scoped
policies, roles, functions and claims remain distinct initial inputs. The custom
validator is limited to the documented bundled vocabulary, with unsupported
keywords rejected; it is not a general schema implementation.

Important downstream limits: do not give actor policies or UI the trusted
Scenario owner/audit_data; runtime actions require fresh KnowledgeStore views.
Historical_scope is a prose rationale, not an option-selection oracle. Adaptive
retry and selected categories need explicit behavior in AE-009/010; public
alternatives are not implemented rules yet. Live grant/policy lifecycle, outcome
rules and feedback still need their campaign activities. Data/code packaging is
unproven until AE-032. No architecture, real payment, full-MVP, comprehension,
publication or integration acceptance is implied by this input gate.
