# ADR-002 — Passive Godot 2D projection

- Status: product constraint recorded; bounded passive component observed on native host; frame/player gates pending
- Date: 2026-10-09
- Scope: AE-021 passive preview
- Decision owner and review activity: product brief; AE-021 Codex worker self-review
- Related assumptions: MA-14, MA-15, MA-16; no superseded ADR

## Context and uncertainty

AE-020 publishes public roster, channels, transfer lifecycle, work and assurance.
The [owner window revision](../campaigns/mvp/revisions/2026-10-09-window-milestone.md)
brings a passive window forward. Godot 4 / 2D / GDScript is a product constraint;
legibility and live responsiveness remain hypotheses requiring real rendering.

## Alternatives and criteria

A custom Node2D graph with scrollable text panels keeps the projection small and
IDs inspectable. A richer UI framework, final art, 3D and management controls are
deferred. Recorded fixture playback complements live HTTP; it cannot prove sockets,
a desktop window, participant comprehension or frame-rate independence.

## Decision and consequences

Use the preinstalled Godot **4.7.2** compatibility renderer. Python's real
DeliveryService prepares explicit agent profiles, channels, transfers and work.
A bounded Python owner schedules three PreviewSession steps independently of
rendering, owns the server and Godot child, and cleans both on exit/error/signal.
Godot sends only snapshot/events requests, validates batches atomically and refreshes
public state. A refresh retains the event cursor so facts between polls are not
skipped; a disconnect performs at most three resnapshot retries. Run mismatches and
capacity exhaustion require restarting the preview.

Roster, directed links, terminal message states, proposal IDs and assessment statuses
come from Python. Pending message animation stops before the recipient, regardless
of elapsed render time. Receipt/loss markers require their recorded fact. Text uses
explicit public fields; private contents, hidden functions and world answers never
enter the presentation. Scroll panels retain readable public IDs without inventing
missing lifecycle state. Snapshot identities are displayed, not treated as saves.

## Evidence and validation

[Review and commands](../../research/experiments/AE-021/review.md),
[actual red](../../research/experiments/AE-021/red.json),
[smoke probe](../../godot/tests/smoke_probe.gd) and
[Python recording/bootstrap](../../research/experiments/AE-021/live_preview.py).
Headless tests establish projection/admission behavior with real Python fixtures.
Worker kernel sockets and X11/Wayland access are denied. Live rendering, viewport
legibility and real client/server recovery await operator validation; no fake desktop
capture or participant records were substituted.

## Revisit trigger

AE-022 measures responsiveness and frame independence. Revisit on lost events,
unsupported snapshot evolution, a legibility failure or a measured transport/lifecycle
problem. Controls remain behind AE-017/018/019 and AE-023 dependencies. No domain,
architecture, integration or publication acceptance follows from this ADR.

## Independent native validation

Root operator review preserved the worker result and compared actual live Godot
IDs/statuses with Python. Native OpenGL with V-sync enabled did not refresh or
capture; X11 alone did not resolve it. Disabled V-sync did, and the project now
caps presentation at 60 FPS with V-sync disabled. This is a host-observed
workaround, not a universal renderer finding; revisit on other hardware.
Recorded public state remains Python-owned. Scroll refresh and historical-send
regression bugs were reproduced by failing probes and corrected. Default preview
lifetime is until user close, with owned cleanup; finite diagnostics still fail
on incomplete/mismatched projections. See the
[operator review](../../research/experiments/AE-021/operator-review.md).
