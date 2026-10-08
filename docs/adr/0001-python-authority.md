# ADR-001 — Python is authoritative and independently reusable

- Status: accepted as an existing product constraint; implementation unverified
- Date: 2026-10-08
- Scope: system boundary and execution contract
- Decision owner and review activity: Agent Empires product brief; recorded by
  the AE-001 Codex worker, with worker self-review. No independent architecture
  acceptance or human review is claimed.
- Related assumptions: MA-14; no superseded ADR

## Context and uncertainty

The campaign requires headless experiments and eventually a Godot 4 presentation
of the same model. Rules in both runtimes would make the displayed game and
research results disagree. Campaign sections 4 and 7 already require Python to
own simulation time, rules, randomness and causal history. This ADR records that
constraint; it does not approve the proposed aggregate split or transport.

At AE-001 there is no simulation package, Godot project or dependency suite. The
system interpreter is 3.14.4 while the controller uses 3.12.13. Available runtimes
must be distinguished from the runtime chosen for reproducible project work.

## Alternatives and criteria

| Alternative | Consequence against headless reuse and one source of rules |
| --- | --- |
| Python owns the model; Godot and transport are adapters | Same application services can support experiments and a game; explicit serialization/lifecycle boundary needed later |
| Godot owns the model | Convenient presentation integration, but violates independent Python reuse and makes headless experiments depend on the renderer toolchain |
| Split or duplicate rules | Easy local UI shortcuts, but requires synchronization and permits contradictory outcomes; rejected |

## Decision and consequences

Keep authority in Python. Dependency direction is adapters -> application ->
simulation. Simulation does not import application, adapters, Godot, UI, HTTP,
the campaign controller or external services. Headless experiments call the same
application services without transport. Godot may interpolate presentation and
submit commands; it cannot advance domain time from frames, sample outcome RNG,
validate domain rules independently or maintain a competing authoritative state.
Adapters translate versioned commands, snapshots and event batches.

The [development contract](../development.md) selects CPython 3.12.13 and uv with
a committed `uv.lock` and an ignored checkout-local `.venv`, introduced in AE-003.
The controller keeps its own environment. Pinning execution versions bounds
future replay claims; it does not establish determinism before tests exist.
AE-002 may simplify logical contexts. AE-020 chooses transport after a spike;
no HTTP framework, event-sourcing framework or database is selected here.

## Evidence and validation

- Product constraint: [campaign sections 4–7](../mvp-campaign.md#4-key-design-principles).
- Runtime and controller checks: [AE-001 observations](../../research/experiments/AE-001/observations.json).
- Disposition and negative findings: [AE-001 review](../../research/experiments/AE-001/review.md).

Godot and godot4 were not found on PATH; none was installed. The missing baseline
AE-001 receipt failed as expected. Inspect/render succeeded without launching
another worker. There is no engine to import, so no executed import-boundary,
replay or frame-rate-independence proof exists. This acceptance records the
specified constraint only; AE-001 has no architecture decision gate.

## Revisit trigger

AE-003 tests deterministic execution within the selected runtime; AE-007 and
AE-020 must test import direction and headless reuse; AE-022 tests that rendering
cadence does not alter canonical history. Revisit if those tests expose a boundary
problem or a product decision explicitly changes Python authority. A runtime
upgrade requires replay revalidation under the development contract. Failed
experiments remain visible and do not justify silently moving rules into Godot.
