# Planning validation receipt

Date: 2026-10-08. Scope: authored campaign, controller compatibility, planning
consistency and evidence-check behavior. This is **not** an AE-001 activity receipt,
an architecture acceptance, a simulation result, or an MVP completion claim.

Repository baseline: `d8b4116` on `main`, initially clean. Controller source:
`/home/senanayake/Dev/campaign-controller` at
`3c064387fb3bda108ff86dcddc6955a7568f22d8`; no controller edits.

| Check | Observed result |
| --- | --- |
| Repository inspection | Original README and ignore file read, license identified, tracked files and history inspected; no source, planning documents, project `AGENTS.md` or ancestor `AGENTS.md` found. |
| Controller schema | JSON Schema Draft 2020-12 validation passed against the controller's actual `schemas/campaign.schema.json`. |
| Controller `inspect` | Exit 0; campaign `agent-empires-mvp`, target `.`, active queue `AE-001`, queue status `pending`, 35 queues, independent validation. |
| Controller load and prompt rendering | All 35 queues loaded and rendered through `load_campaign_config` and `codex_loop.render_codex_prompt`; each includes ID, objective, non-goals and required activity check. |
| Actual CLI prompt rendering | Exit 0 for AE-001, AE-002, AE-003 and human-study gate AE-029. No worker launched. |
| Document/manifest agreement | `python3 scripts/check_campaign.py` passed: 35 activity IDs, nine required fields, matching titles/objectives/scopes/acceptance/tests/dependencies, complete sections 1–15, acyclic dependency graph. |
| Evidence failure at baseline | `--activity AE-001` exited 1 because its real completion receipt does not exist. This is expected; implementation remains unstarted. |
| Validator positive fixtures | Valid plan and structurally valid synthetic receipt accepted in a temporary directory. Synthetic fixture is explicitly not a real campaign result. |
| Validator negative fixtures | Ten rejected cases: duplicate IDs, objective drift, missing field, unknown dependency, dependency cycle, absent receipt, non-pass disposition, stale artifact hash, escaping evidence path, and missing human-study records. |
| Python helper | Standard-library checker parsed successfully with system Python; no simulation implementation added. |
| Whitespace | `git diff --check` passed. |
| Document links | All 15 relative Markdown file links across nine documents resolved. |

Negative/positive structural fixture tests ran in an automatically removed temporary
directory. No synthetic receipt or participant record was written to the actual
campaign evidence directory. The helper's parsing expression was corrected during
validation before the final successful checks; an initial wrong controller import
in the validation harness was corrected to the actual `codex_loop` module.

Reproduce inspection and CLI rendering with the commands in the [handoff](README.md).
Schema validation used the already installed system `jsonschema` package. The
campaign's ordinary checker itself needs no third-party dependency. No dependencies
were installed for this planning work.

## Review conclusions and remaining limits

- The domain model keeps closure, authority and evidence independent; Decision
  provenance, Actor/Role/Function separation, private world state and the three
  learning loops have explicit counterexample activities.
- Early causal comprehension and a paper/terminal choice test precede Godot.
  World behavior and matched-profile controls challenge actor-kind punishment.
- Assumption Debt is diagnostic and removable. All model parameters are currently
  uncalibrated; proposed empirical claims remain unsupported.
- The manifest has explicit paths and independent acceptance commands. Later code
  and Godot tests are **planned, not run**. Actual human studies have not occurred.
- All activities remain pending. The controller's legacy promotion/completion
  semantics and unconfigured model-router review are disclosed. Domain review is
  not guaranteed by a passing receipt schema or by a queue stage named “review.”
- The campaign is suitable for inspection and future bounded, supervised execution.
  Unattended continuation through conceptual/human gates requires native pinned
  decision gates based on real reviewed evidence. AE-030's repair scope must be
  bound to actual findings before its implementation paths are enabled.
- No Godot executable was available on PATH. No game build, worker, state database,
  service, cloud resource, deployment, commit or publication was created by this task.

Independent scientific validity, gameplay quality, transport responsiveness,
packaging and the MVP definition of done remain the work of the campaign.
