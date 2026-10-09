# Independent root review of AE-020

Reviewed application validation/idempotence/capacity, HTTP parser/body/time bounds,
read-only detached projections, redaction, cursor atomicity, import direction,
source/self-review evidence and actual negative tests. All worker input/artifact
hashes matched before edits; exact receipt and changed source/docs were archived.

Three actual failing tests exposed the missing public graph needed by AE-021.
Added only event-derived channels and message lifecycle projections within AE-020
application/contract scope; no simulation code or domain events changed. Queries
never call the lazy communication accessor. Propositions, private source lineage,
hidden functions, draws and world state remain excluded. Reconnect restores actual
status and active edges; returned data cannot change domain history.

37 actual transport contracts pass on kernel sockets; full suite: 524 pass.
Separate-process real loopback: 300 measurements, nearest-rank p95 0.490115 ms.
Worker socket/Git failures remain historical. One sequential client, small workload,
4096-ID cache and in-memory history are preview limits. Godot/frame independence,
management controls, participant comprehension and empirical calibration remain
unproven. Root accepts this bounded transport activity for passive AE-021.
