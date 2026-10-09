# agent-empires
Strategize. Build your empire. Control your agents.

Agent Empires is a 2D management simulation about how organizations turn uncertain
intent into decisions, software, outcomes, and learning.

The current build contains a deterministic headless Python simulation and the
PaymentCo causal slice: incomplete work, decision provenance, implementation,
multidimensional verification, explicit deployment and delayed payment outcomes.
It includes actors, knowledge holdings, communication channels, authority and
reproducible event histories. Godot presentation and the complete playable MVP
remain future campaign work.

The [MVP development campaign](docs/mvp-campaign.md) defines the risk-ordered
activities. See [build progress](docs/build-progress.md) for accepted activities,
local integration details and limitations. AE-001 through AE-010 are accepted;
AE-011 engineering is integrated. Under the [owner-approved revision](docs/campaigns/mvp/revisions/2026-10-09-owner-feedback.md), development continues with owner feedback; unfamiliar-player comprehension and enjoyment are tested at the playable prototype. The initial audience is engineers, managers and other IT professionals. Prepared materials include the [reader instructions](research/experiments/AE-011/packet/reader/instructions.md)
and the facilitator's [collection protocol](research/experiments/AE-011/protocol.md).

From this checkout, select the pinned runtime and run the tests and retained
experiments without overwriting evidence:

```bash
uv sync --locked --python 3.12.13 --group dev
uv run --locked --python 3.12.13 --group dev python3 -m pytest -q
uv run --locked --python 3.12.13 --group dev python3 experiments/paymentco_slice.py --verify-against research/experiments/AE-010
uv run --locked --python 3.12.13 --group dev python3 experiments/trace_report.py --verify-against research/experiments/AE-011/packet
```

The current engineering checkpoint passes 316 tests and reproduces 357 seeded
PaymentCo cases. Parameters are explicitly invented conceptual/gameplay values;
these experiments do not establish effects in real organizations or reader
comprehension. See the [model assumptions](docs/model-assumptions.md).

The [Campaign Controller handoff](docs/campaigns/mvp/README.md) describes execution
policy. The committed manifest is the original plan; the live controller database
and execution configuration are recorded in the build-progress ledger. Resume
from that durable state rather than restarting the original manifest.
