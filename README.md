# Agent Empires

A 2D management simulation about how organizations turn uncertain intent into
decisions, software, evidence and outcomes. Python owns the deterministic,
headless simulation; Godot presentation is still ahead in the campaign.

The [risk-ordered MVP campaign](docs/mvp-campaign.md) is accepted and locally built
through AE-015. The combined PaymentCo model gate covers inference, costed
clarification, separate learning loops, explicit authority and delayed outcomes.
It retains failed policies and harmless unsupported choices. The Assumption Debt
scalar was rejected for gameplay after counterexamples; concrete components,
behavior and causal history remain. [Build progress](docs/build-progress.md)
records delivery, evidence and remaining limits.

The owner approved development with their feedback and unfamiliar-player testing
at the playable prototype. The audience is engineers, managers and other IT
professionals. Comprehension and enjoyment are still untested.

```bash
uv sync --locked --python 3.12.13 --group dev
uv run --locked --python 3.12.13 --group dev python3 -m pytest -q
uv run --locked --python 3.12.13 --group dev python3 experiments/model_matrix.py --verify-against research/experiments/AE-015
uv run --locked --python 3.12.13 --group dev python3 experiments/trace_report.py --verify-against research/experiments/AE-011/packet
uv run --locked --python 3.12.13 --group dev python3 scripts/check_campaign.py --activity AE-015
```

The latest independent checks pass 442 tests and reproduce all 60 matched
seed/world groups. Earlier source-bound manifests become historical after
legitimate extensions; do not overwrite their evidence. Parameters are invented
conceptual/gameplay values, not empirical organizational proof. See the
[model assumptions](docs/model-assumptions.md) and [controller handoff](docs/campaigns/mvp/README.md).
Resume from the durable controller state recorded in the ledger. Replacement,
Godot controls, the short play loop and genuine player validation remain to build.
