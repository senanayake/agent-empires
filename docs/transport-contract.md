# Passive preview transport v1 (AE-020)

One standard-library HTTP adapter binds **127.0.0.1 only**, with one sequential
consumer. It translates JSON into `application.commands.PreviewSession`; domain
rules/time/history remain in `DeliveryService` and simulation. No new dependency.
The [window revision](campaigns/mvp/revisions/2026-10-09-window-milestone.md) still
requires AE-017/018/019 before management controls. This interface exposes none.

From the checkout root, using the locked `.venv`:

```sh
python3 -m agent_empires.adapters.transport.http --run-id preview-unique-1 --port 0
```

The single stdout readiness record reports version/run/host/selected port. Choose
a new run ID for every new process. Trusted startup loads PaymentCo, seed 0 by
default (`--seed` overrides), and starts Jin's real work as `preview.work`. Initial
state is paused. This is a delivery preview, with no shipping/world exposure or
invented transfer behavior. The caller owns process startup/termination; Ctrl-C
closes the listener. Packaging/owned-child cleanup belongs to AE-032.

## Requests and acknowledgments

`POST /command`, `Content-Type: application/json`, one positive Content-Length,
UTF-8 body at most 65,536 bytes. Chunked bodies, duplicate keys, non-finite JSON,
truncated/invalid bodies and unsupported versions are rejected. Connections close
after each response; reads time out after two seconds. No public-service claim.

Every command has exactly these fields:

```json
{"version":1,"run_id":"preview-unique-1","command_id":"client.1","operation":"snapshot","args":{}}
```

IDs/operation are nonempty strings, at most 128 characters. Version and numeric
arguments are integers, excluding booleans. Command IDs are globally unique within
a run; one client/one outstanding command is the preview's supported usage.

| Operation | Exact args | Behavior |
| --- | --- | --- |
| `snapshot` | `{}` | Detached authoritative public state at the current cursor |
| `events` | `{"cursor":0,"limit":256}` | At most 1–256 contiguous events, starting at next sequence `cursor` |
| `pause` | `{"paused":true}` or false | Change scheduling permission; never advance domain time |
| `step` | `{}` | While paused, call the existing service's next-completion dispatcher once |
| `advance` | `{}` | While resumed, explicitly call that same dispatcher once |

There is no background clock. Resume permits explicit `advance` requests; it does
not derive ticks from frames/wall time. A step can drain messages/tombstones before
a live completion; it is not necessarily one fact or one tick. An empty queue
leaves time/history unchanged. There are no replace/clarify/document/connect/ship
commands. Display pacing remains a future AE-021/022 concern.

Accepted HTTP 200 acknowledgments contain `version`, `run_id`, `command_id`,
`ack_id` (`<run>:ack:<command>`), `status: accepted`, current `tick`, `cursor` and
`result`. Playback results report `changed`; pause reports `paused`. Rejected
HTTP 400 acknowledgments contain the same identity fields and `status: rejected`,
`error`. An unidentifiable malformed command has null command/ack IDs. Unknown
paths return 404; other HTTP methods receive the standard server's 501 response.

Errors: `malformed_command`, `incompatible_version`, `wrong_run`,
`unknown_operation`, `duplicate_id`, `invalid_cursor`, `not_paused`, `paused`,
`session_capacity`. Rejections do not mutate domain state or history.

Valid-envelope commands (including rejected operations/arguments) reserve their
ID. The identical parsed JSON command returns the **original acknowledgment**,
including its old cursor/snapshot, without executing twice. Different content
with that ID is rejected. Reordering object keys is equivalent. Returned objects
cannot mutate cached responses. Invalid envelopes/versions reserve nothing. The
cache admits 4,096 IDs per run, then rejects new IDs while retaining retries;
this provisional preview bound needs reconsideration for longer polling sessions.

## Snapshots and events

Snapshot fields: `version`, `run_id`, `snapshot_id`, `scenario_hash`,
`model_version: delivery-preview-v1`, `tick`, `cursor`, `paused`, `goal`,
`work_item`, current `roster` (ID/kind/team/formal role), decision IDs/alternatives,
and completed proposals (ID/actor/completion tick/assurance dimensions).
`snapshot_id` is `<run>:snapshot:<SHA-256 of canonical public state>`; identical
state yields identical identity. Reconnect retains verification pass separately
from unknown validation/outcome fitness. Snapshots are projections, not saves.

Batch fields: `version`, `run_id`, `batch_id: <run>:batch:<cursor>:<next_cursor>`,
`cursor`, `next_cursor`, `head_cursor`, `events`. Cursors are next zero-based domain
sequence numbers; `cursor == head_cursor` yields an empty batch. A future cursor
is rejected. Each event carries its original `<run>:event:<sequence>` ID,
`sequence`, `tick`, `schema_version`, public `event_type`, command/correlation IDs
and a whitelisted payload. Private/unknown fact types become `Redacted` with empty
payload and null command/correlation IDs. Placeholders preserve sequence coverage.

No knowledge content/catalog, hidden function coverage, world answers/parameters,
channel draws, source lineage or private causal graph crosses this preview.
Verification exposes dimension/status/method, preserving unknowns. New fact types
are private by default. Public IDs can reference actors/proposals; these are not
correctness or authority grants. Rich actor-accessible inspection belongs to AE-026.

The consumer installs a fresh snapshot atomically, records its run/cursor, then
accepts batches only with matching version/run/start cursor, contiguous ordered
sequences, matching event IDs/schema, consistent end/head and batch ID. Duplicate,
gapped, reordered or old-run batches are discarded in full: request a new snapshot.
`EventCursor` implements this admission rule. Polling/pausing changes no domain facts.

## Disconnect and measurement

A disconnect does not advance time or undo completed commands. If an acknowledgment
is lost, resend the identical command ID/content; then request a **new-ID** snapshot
for current state. Reconnection to the same process retains state/cache. Process
loss loses both; launch a new run and discard old cursors. Persistence is AE-031.
The server retains history in memory; no streaming/backpressure platform is added.

[measurement.json](../research/experiments/AE-020/measurement.json) records hardware
and a real separate-process loopback attempt: **unavailable**, socket creation denied
by this worker sandbox. The target p95 below 250 ms is unverified. The separate
[handler diagnostic](../research/experiments/AE-020/handler-measurement.json) measured
300 serialized requests at p95 **0.403191 ms**, excluding sockets/process scheduling.
It cannot establish the loopback budget or Godot responsiveness.

To collect independent runtime evidence without overwriting negative findings:

```sh
python3 research/experiments/AE-020/benchmark.py --output /tmp/ae020-loopback.json
```

The probe records one real work-completion acknowledgment, 30 warmups, 300 mixed
serial requests and nearest-rank p95. It refuses existing outputs. The workload is
small and mostly polling/empty steps. HTTP is the provisional single adapter:
explicit reconnect/lifecycle and dependency-free request framing are sufficient
for this spike. JSONL is deferred, without a comparative speed claim. Revisit if
controller loopback p95 fails, or AE-021 demonstrates lifecycle/client trouble;
benchmark a second adapter only on a demonstrated transport criterion failure.

## Independent operator validation

The root operator ran the enabled real loopback tests in the unrestricted local
environment: 37 transport tests and 524 full-suite tests pass.
[Real separate-process measurement](../research/experiments/AE-020/operator-loopback-measurement.json)
records 300 requests with p95 **0.490115 ms**, below the provisional 250 ms budget
on the recorded host. The worker sandbox failure remains historical evidence;
this tiny workload establishes neither long-session nor Godot responsiveness.

The public snapshot additionally includes `channels` and `transfers`, derived
only from recorded facts without initializing or mutating communication.
Channels expose ID/sender/recipient/latency; retired edges disappear. Transfers
expose their original TransferSent event ID, endpoints/channel, unit count,
sent/delivery ticks and `pending`, `received` or `lost` status. Resolved ticks
come only from actual KnowledgeTransferred/InformationLost facts. The same
whitelisted facts cross event batches; transfer completion links only to the
public send ID. No item/holding/source IDs, propositions, distortion draws/rules
or hidden functions cross. GDScript may interpolate those messages but may not
predict a terminal status.
