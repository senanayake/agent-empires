# AE-005 channel protocol

Written before tests and implementation; authored toy parameters, no calibration
or participants. Question: can explicit directed sends expose access, delay,
capacity, reliability and cost trade-offs without a privileged answer key?

Use AE-003's clock/history/named RNG and AE-004's current actor views. One message
copies one accessible holding snapshot over one directed edge. Positive integer
latency; finite positive admissions per tick; reject congestion without charging
or queueing. Each admitted message costs integer resource units, even on loss.
Connections may have a one-time cost. No automatic forwarding, retries, broadcast,
route optimization, trust effects or maintenance-cost model.

Predeclare red/green tests for loss 0/1, distortion 0/1, finite delay/capacity,
disconnection/direction, source copies, invalid commands, in-flight departures,
actor relabeling, seed replay and route/cost controls. Distortion replaces a
specified topic/proposition with a specified alternative, preserving declared
source IDs and uncertainty metadata; it does not consult hidden world truth.
Loss and distortion get separate named draws keyed by send command ID, independent
of edge registration and unrelated randomness. Independent failures are assumed;
correlated outages remain untested and must be retained as a limitation.

Experiment seeds: integers 0–31 inclusive. Each run sends four identical-source
messages with stable IDs. Compare (loss, distortion) in (0,0), (1,0), (0,1),
(0.25,0.5), (0.75,0.5). Report every seed, counts, mean/range, canonical histories,
and all failed assertions. Repeat with reversed registration and human/agent
relabeling. No estimate of real-world reliability or comprehension is intended.

Topology fixture: isolated recipient, direct fast costly edge (latency 1,
connection cost 6, transfer cost 4), two-hop cheap route (each latency 2,
connection cost 1, transfer cost 1), and their union. Use loss/distortion 0 for
this control. Measure final access, arrival tick and total spent units. Falsifiers:
disconnected acquisition, free/immediate copy, source inflation, missing outcome
facts, replay mismatch, or a claimed trade-off unsupported by measured costs.
The cheap path should suit budget 4/deadline 4; the fast edge should suit budget
10/deadline 1. These are invented contrasting constraints, not player preferences.

Author results only to fresh output files. Verify by regenerating in temporary
storage and comparing without overwriting evidence. Worker self-review must
separate mechanism consistency from usability and architecture acceptance.
