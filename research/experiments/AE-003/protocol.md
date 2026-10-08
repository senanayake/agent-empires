# AE-003 execution protocol

Recorded before implementation/results. Engineering fixture only, no PaymentCo
rules, participants, empirical parameters or architecture gate. CPython 3.12.13.

Question: do explicit time, ordered commands, named random streams and immutable
facts reproduce identical canonical bytes? Falsifiers: reordered equal-key work,
ambient time/random use, dangling/cyclic parents, mutated historical payloads,
hash-seed-dependent bytes, or unrelated RNG draws perturbing world samples.

Use root seeds 17 and 23; repeat each in fresh objects and processes with
PYTHONHASHSEED 1 and 987. Schedule the same four authored commands, including
equal-time/equal-priority work, then emit a receipt fact for each with a bounded
integer world sample and earlier typed causal links. This is an invented command
fixture, not an application command API or a payment-world experiment.

Controls: change seed (stochastic payloads must differ in these selected runs),
consume an unrelated named stream (world samples unchanged), split clock
advancement (same history), reverse payload map insertion order (same bytes),
and forbid wall clocks/ambient RNG/entropy during replay. Explicitly demonstrate
that an extra draw in the *same* stream changes subsequent samples: named streams
do not alone align counterfactual endogenous draw counts.

First record focused failing tests before implementing primitives. Then run
negative/boundary/invariant cases and the identical focused command to green.
Keep all red output and any failed seeds. Author run manifest, command fixture,
canonical histories and results under this directory. Verification uses temporary
storage and compares to committed evidence without overwriting it. The manifest
binds scenario/fixture version and hash, initial state, command order, seeds,
RNG scheme, source hashes/model version, runtime and lock hash.

Full event-sourced reconstruction, save/resume, rendering cadence, large queues,
cross-runtime replay and independence of real-world sources remain unproven.
