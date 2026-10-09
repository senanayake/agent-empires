# Agent Empires

A 2D management simulation about how organizations turn uncertain intent into
decisions, software, evidence and outcomes. A **live Godot observation preview**
now runs against the authoritative Python simulation.

## Run the preview

Use CPython 3.12.13, uv, and Godot 4.7.2 available as `godot`:

```bash
uv sync --locked --python 3.12.13 --group dev
.venv/bin/python research/experiments/AE-021/live_preview.py
```

The window shows PaymentCo's five departments, ten humans and three agents,
directed communication, real message receipt/loss, work and change proposals,
separate assurance dimensions, and a public event feed. Python schedules the
short demonstration; Godot renders it. Scroll the panels to inspect details.
Close the window to stop its Python owner and clean up the local server.

This is a passive preview. Management actions and the 15–20 minute playable loop
remain campaign work. The campaign controller accepted AE-001–016 and AE-020–021;
AE-017–019 remain required before controls. See [build progress](docs/build-progress.md),
the [MVP campaign](docs/mvp-campaign.md) and [development commands](docs/development.md).

## Validate

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q research/experiments/AE-021/test_preview.py
godot --headless --path godot --import
godot --headless --path godot --script res://tests/smoke_probe.gd
.venv/bin/python scripts/check_campaign.py --activity AE-021
```

Independent evidence includes 524 full-suite tests, 43 focused transport/bootstrap
tests, actual native rendering and matching Godot/Python IDs/statuses.
[The operator review](research/experiments/AE-021/operator-review.md) retains
failed runs, fixes and viewport captures. Earlier source-bound evidence remains
historical after legitimate extensions; do not overwrite it. Parameters are
conceptual/gameplay assumptions, not empirical organizational proof.

The initial audience is engineers, managers and other IT professionals. Actual
player comprehension and enjoyment are still untested. See the
[model assumptions](docs/model-assumptions.md) and [controller handoff](docs/campaigns/mvp/README.md).
