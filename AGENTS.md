# Agent Empires worker contract

Work on the single activity assigned by the controller in its assigned checkout.
Start with [development commands](docs/development.md) and the
[controller handoff](docs/campaigns/mvp/README.md). The repository owns domain
acceptance; Pahanna OS owns execution policy, checkout lifecycle, independent
validation, integration/publication and controller state.

## Before editing

1. Read `docs/mvp-campaign.md` sections 2–8 and the assigned activity,
   `docs/model-assumptions.md`, `docs/adr/README.md`,
   `scenarios/paymentco/README.md`, and the controller handoff.
2. Read that queue in `docs/campaigns/mvp/campaign.json`: dependencies, allowed
   paths, validation commands, timeouts and stop conditions are the work boundary.
   Do not change the manifest or checker to obtain a pass.
3. Review each predecessor's actual artifacts and receipt in this checkout;
   run `python3 scripts/check_campaign.py --activity <predecessor-ID>` and read
   its findings and limitations. A passing hash check cannot replace substantive
   review. Stop on missing, stale, contradictory or non-passing predecessor
   evidence. AE-001 has no predecessors.
4. Check `git status --short`, the branch and the interpreter. Use the Python
   setup in `docs/development.md`; never assume system Python is the project
   runtime. Do not discard another worker's changes.

## Implementation and validation

- Python owns rules, simulation time, seeded randomness, histories and outcomes.
  `simulation` may use the standard library and explicitly selected domain
  dependencies; it must not import `application`, `adapters`, Godot, UI, HTTP,
  controller code or external services. Application imports simulation;
  adapters import application. See [ADR-001](docs/adr/0001-python-authority.md).
- CPython **3.12.13** is the selected execution baseline. AE-003 creates
  `pyproject.toml`, committed `uv.lock` and a checkout-local ignored `.venv`.
  Use uv and locked synchronization thereafter. Keep the controller environment
  separate. Do not install Godot for early activities.
- For behavior changes, add a focused failing test, record the actual failure,
  implement the smallest change, then refactor with tests green. Use boundary,
  negative, invariant, metamorphic, integration and seeded simulation cases when
  they test meaningful behavior. Do not add tests that merely mirror prose or
  implementation. Documentation-only activities need command checks and review,
  not a fabricated TDD cycle.
- Run the assigned manifest validations from this checkout's root, including
  `python3 scripts/check_campaign.py --activity <ID>` and `git diff --check`.
  Missing future tests are not passes. Record failures, unavailable tools and
  skipped checks honestly; follow the packet's independent-validation semantics.
- Record consequential decisions with `docs/adr/template.md` and update the ADR
  register. Distinguish product constraints, proposed hypotheses and decisions
  supported by evidence. Never claim empirical calibration from toy parameters.

## Evidence and handoff

Write `docs/campaigns/mvp/evidence/<ID>.json` using the handoff receipt contract;
keep raw results under `research/experiments/<ID>/`. Bind current input and
artifact SHA-256 hashes after edits settle. Identify the actual reviewer,
including worker self-review; do not imply an independent or human review.
Preserve negative findings, failed seeds and unsupported claims. Human-study
records must come from actual participants.

Commit completed in-scope work locally. Push is disabled for this campaign,
including worker branches, despite the rendered prompt's generic push wording.
The controller owns promotion to `build/mvp`; a worker commit or passing tests
does not prove integration or publication. Update the handoff ledger when in
scope; never edit controller state or declare campaign completion.

Emit progress at least every 60 seconds while working. End with the packet's
machine-readable final report exactly once. Recommend a successor only after
the assigned work is complete; do not execute it. Workers do not invoke controller
launch commands. Future operators follow the bounded launch policy in the handoff.
