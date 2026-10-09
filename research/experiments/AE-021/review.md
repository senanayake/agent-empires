> Historical worker self-review at the original attempt. Current lifetime, rendering and runtime disposition are in [operator-review.md](operator-review.md) and [development commands](../../../docs/development.md). The original worker document is preserved byte-for-byte under `before-operator-review/`.

# AE-021 scoped ledger and worker self-review

AE-020 is present and substantively reviewed: current source projections, protocol,
37 independently passed transport contracts / 524 suite tests, real 300-request
p95 0.490115 ms, and operator review. Entry hash check passes; its worker socket/Git
failures remain historical and operator-reviewed delivery resolved that handoff.
Its receipt and the shared docs changed here are archived under `entry/`. No gate
or architecture acceptance is inferred. Shared build/handoff ledgers are outside
AE-021's exact write scope; this file is the activity ledger.

The view projects the five PaymentCo departments, ten humans and three explicitly
registered agents with different authored profiles. Directed edges are actual
ChannelConnected facts. The bootstrap sends three accessible holdings through real
Communication APIs: two delivered messages and one intentionally loss-probability-1
engineering counterexample. Those are toy preview interventions, not fabricated
facts or calibrated rates. Python starts three jobs, then calls PreviewSession step
three times. Nothing ships and no world exposure/hidden-answer inspection occurs.

`red.json` records the smoke probe failing on the missing projection scripts.
`first-green-attempt.json` passes assertions but preserves user-directory write
errors. `green.json` / `probe.json` pass using writable temporary XDG directories.
Tests cover complete roster/state/proposal IDs, ordering/duplicate/gap/old-run/schema
rejection, atomic cursor admission, empty batches, resnapshot bounds, the refresh
cursor race, pending messages after a large render-time jump, actual loss/receipt,
reconnect restoration and separate verification-pass/validation-unknown statuses.
Four Python checks regenerate the fixture, prove passive polls do not change history,
exercise all three real agent profiles and check error cleanup using explicitly
mocked resources. The initial mock lacked a PID; that test-harness failure is retained
in `python-test-first-attempt.json`, not reported as a domain regression.

## Independent runtime procedure

From checkout root after locked Python synchronization and the required Godot import:

```sh
.venv/bin/python research/experiments/AE-021/live_preview.py --duration 30 --capture /tmp/ae021-live.png
```

Default run IDs are unique per launch; `--run-id`, `--seed`, `--port` and `--godot`
configure the owner. The owner prints its endpoint, run ID and child PID. The window
shows connection status and prints each changed displayed snapshot ID plus actor,
proposal and transfer IDs/statuses. At exit the owner requires three real completions
and compares the final Godot record with Python. `--duration` is bounded to 8–300
seconds and must allow three steps plus polling; `--step-seconds` is 2–10 seconds,
default 3. These are engineering pacing budgets, invented and uncalibrated, not
simulation parameters. Close the window or Ctrl-C to stop; an early exit is recorded
as incomplete validation. Normal timeout terminates/waits for the child, with bounded
kill fallback, and closes the server. No orphan/background server is intended.

For an independently started AE-020-compatible prepared server, use its readiness
endpoint and exact run ID:

```sh
godot --path godot -- --endpoint=http://127.0.0.1:PORT/command --run-id=RUN_ID
```

That client only reads; the external Python owner must schedule work. No snapshot
request steps time. Requests are sequential and paced; after three reconnect retries
the view retains its last public state with an explicit disconnected status. Wrong
run/version or exhausted 4096-ID server capacity requires a fresh owner/client run.
The bounded default preview stays well below that cache. No process restore claim.

Offline recorded playback:

```sh
godot --path godot -- --fixture=res://tests/fixtures/paymentco.json --capture=/tmp/ae021-fixture.png --capture-after=7
```

Capture awaits RenderingServer.frame_post_draw and saves only the project viewport;
it never captures the desktop. Live bootstrap capture occurs at 11 seconds; keep
`--duration` at least 15 when requesting one. Scroll text panels to inspect all links,
messages and assessment dimensions. Inspect the 1440×1000 viewport for five populated
departments, all 13 actor IDs and readable roles, human circles/agent diamonds,
directed arrows, three message IDs with actual terminal status, Work Item `work.retry`,
three proposal IDs, verification pass with validation/outcome unknown, and ordered
public event IDs. Pending markers stop before recipients. Loss uses an X only after
a loss fact; no particle predicts loss or knowledge acquisition. Inspect both a pending
frame and a completed frame; compare the printed IDs with the owner's final snapshot.

## Negative results and limits

Worker `live-headless.json` fails at kernel socket creation (PermissionError).
`window-attempt.json` fails at both X11 and Wayland initialization. No visible window,
viewport PNG or text-legibility observation is claimed. Import returns zero with
sandbox socket/editor-path diagnostics; writable XDG paths remove filesystem errors
but do not authorize sockets. On a restricted worker, set XDG_DATA_HOME,
XDG_CONFIG_HOME and XDG_CACHE_HOME to writable subdirectories under `/tmp`; do not
change HOME or use controller packages. The independent operator must run the live
procedure and inspect the viewport in the actual desktop environment.

Self-review confirms read-only GDScript requests and a public-field whitelist for
visible text. Rich panels scroll; the event feed retains the last 120 text rows while
sequence IDs track admitted facts. Snapshot summaries do not invent unprojected work
lifecycle fields. Polling/animation tests are bounded engineering evidence; full
frame-rate independence, long-session responsiveness, participant comprehension,
enjoyment, empirical calibration, domain/architecture acceptance and integration or
publication remain unproven. AE-022 is the proposed successor only after independent
acceptance and required local delivery. No successor was executed or launched.

## Local delivery

The single authorized staging attempt returned exit 128: shared worktree
`index.lock` could not be created on the read-only Git metadata filesystem.
[delivery.json](delivery.json) preserves the exact command/error. No retry, local
commit, push, remote/hook change, controller launch or integration occurred. Source
and reviewed hash receipt remain available for the operator's separate hash-reviewed
delivery retry. Worker final status is failed for required delivery, independent of
the passing source checks; no successor is recommended by this attempt.
