# AE-016 runtime integration scope correction

Root operator correction under the owner's existing build/continue authorization,
2026-10-09 UTC. This changes implementation paths, not product acceptance or the
owner-approved feedback sequencing. No new owner response is claimed.

At source commit `9514a85`, a real DeliveryService preflight starts Sarah's work,
records her departure through KnowledgeStore.depart_actor at tick 0, and still
produces her ChangeProposal at tick 5. Delivery captures an initial roster/profile
map and has no live actor-registration/replacement bridge. KnowledgeStore and
Communication also lack public lifecycle operations for dynamic registration and
channel retirement. A detached replacement record would not resolve those real
execution effects. [The actual probe](../../../../research/experiments/AE-015/runtime-scope-entry/preflight.json)
is retained; it adds no simulation rule or invented participant result.

AE-016 already requires updates to holdings, membership, authority and channel
endpoints plus documented pending-work behavior. Allow the smallest public
lifecycle APIs in knowledge.py, communication.py and decisions.py and the
application/services.py bridge alongside organization.py. Document composition
in simulation-model.md. Keep domain replacement rules in simulation; application
coordinates existing owners and live capability data. Do not write another
owner's private registries, monkeypatch methods or create a second clock/store.
Cancel unfinished departed-actor work explicitly, retaining history/resources;
completed artifacts and admitted in-flight knowledge snapshots follow documented
rules. New actors must be able to execute real work from current access/profile.

Tests must reproduce the observed departure bug before fixing it, check real
new-actor execution and rejected-command nonmutation, and run relevant existing
lifecycle/delivery regressions. No API transport, UI, automatic knowledge/function
or authority inheritance, damage timer, incentive economy or future-stage transfer
mechanic belongs in this correction. Acceptance thresholds remain unchanged.

Update campaign document and manifest together; sync only the selected queue's
scope/allowed paths into external execution configuration. Preserve the accepted
AE-015 receipt and old planning inputs byte-for-byte at runtime-scope-entry before
rebinding exactly those two planning input hashes. Its source/results/protocol
remain unchanged, and this correction is not new experimental evidence. The
controller database remains authoritative and is not edited directly.
