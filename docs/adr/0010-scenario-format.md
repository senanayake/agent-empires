# ADR-010 — Versioned JSON scenario inputs

- Status: proposed; implemented and worker tested, no architecture acceptance
- Date: 2026-10-08
- Scope: application scenario boundary
- Decision owner and review activity: assigned AE-008 worker self-review
- Related assumption IDs: MA-01–08, MA-11–15; no superseded accepted ADR

## Context and uncertainty

The campaign proposes YAML but explicitly permits choosing JSON in AE-008.
PaymentCo needs inspectable finite inputs, parameter provenance and an access
boundary. Stored claims must not become world truth or automatically available
knowledge. No payment calibration, user study or outcome rules exist yet.

## Alternatives and criteria

Restricted YAML permits convenient authoring but requires a parser and a precise
restriction of tags, aliases, duplicate keys and implicit scalar types. JSON is
more verbose but supplies one standard-library representation. Python input
modules risk executing rules while loading. A full JSON Schema library offers
broader validation but adds a dependency for an intentionally fixed vocabulary.

## Decision and consequences

Use `scenarios/paymentco/scenario.json`, replacing `scenario.yaml`, with a
Draft 2020-12 schema that external tooling can inspect. The standard-library
loader evaluates only its bundled schema's explicit vocabulary (local `$ref`,
objects, required/closed properties, arrays and uniqueness/length, primitive
types, enum, string pattern and numeric minimum). Unsupported assertion keywords
raise errors. This is not a general JSON Schema implementation. No dependencies
or lockfile changes are needed. Typed reference checks and parameter-unit/range
checks supplement the structural schema.

Reject non-UTF-8/non-JSON input, duplicate object keys, nonfinite/bool numeric
parameters and incompatible schema/model/scenario versions. Compute SHA-256 over
exact input bytes; optionally require the caller's expected hash. Version and hash
serve different purposes. Trusted run manifests must also bind schema, code/model,
runtime, selected world, seed/RNG contract and ordered commands. Do not embed a
self-referential file hash. Formatting changes intentionally invalidate identity.

Operational numeric inputs use parameter references with the full assumptions
register provenance record. Empirical classification is unsupported in v1.
Actor kind and profile do not grant knowledge or authority. Scoped root grants
are trusted authored organization inputs, not authenticated legitimacy. Policies
reference a matching actor/grant/scope/option and a separately held claim; they
are not world truth. Delegation lifecycle remains the AE-006 engine's job.

The owner retains private audit inputs. Detached actor projections include only
explicitly accessible holdings and allowlisted public context. Simulation imports
remain directed inward. Loading initializes a fresh knowledge store, not work,
world outcomes, authority enactment or communication. Runtime services must use
live views rather than reusing the loader's initial snapshot.

## Evidence and validation

[Focused tests](../../tests/unit/test_scenarios.py) and the independently authored
[Jin fixture](../../scenarios/paymentco/jin-snapshot.json) cover structural,
reference, boundary, redaction and actor-kind/world-change controls.
[Review](../../research/experiments/AE-008/review.md) retains actual red/green
outputs, including initially accepted UTF-16/future-version inputs and missing
public goal values. Worker checks support a bounded input contract, not human,
payment, architecture, integration or publication acceptance.

## Revisit trigger

Adopt a pinned schema library if a required keyword expands beyond this evaluator;
prove parity before changing validators. Revisit the data model when AE-010 world
rules or AE-013 learning need new semantics. Bundle schema/data explicitly during
AE-032 packaging; current lookup assumes the repository layout. Review live
snapshot projection in AE-020/026. Bump format/model version for incompatible
changes instead of accepting future data silently.
