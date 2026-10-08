# AE-002 tabletop: challenge the Decision boundary

Date: 2026-10-08. Author and reviewer: assigned AE-002 Codex worker, **self-review**.
Method: manually authored counterexamples and forward/backward event walks. No
participants, executable simulation, random seeds or calibrated parameters were
used. All outcomes below are stipulated toy fixtures, not measured payment data.

## Protocol and review criteria

Before constructing the traces, use these falsifiers: a selected choice must not
create authority/evidence; a grant must not imply learning; a conformant authorized
policy may fail a goal; copied sources must not become independent; missing
justification must not itself cause harm. Reject a model that needs a global
correctness flag or private World facts in actor knowledge to explain these cases.
Compare a heavy Decision aggregate with a small versioned record referencing
separate owners. Walk each case backward as well as forward to expose missing
causes, stale subject versions and information appearing without delivery.

Notation: owners G/O/K/D/W/A/L and invariants I1–I9 are defined in
[the domain model](../../../docs/domain-model.md). Each case is an independent
fixture; `Tn.0` is its authored initialization fact containing the stated actors,
grants, holdings, goal, policy, World/workload and any pre-existing sources.
`Tn.k` is the fact ID and sequence k; `tick` is an illustrative integer, not a
calibrated delay. All listed parents are earlier: `d` direct modeled cause,
`s` supporting evidence/justification, `a` association. Other version refs are
immutable payload refs; absence from a parent's accessible view gives no access.
These sketches specify a history contract, not proof of event-sourced replay.

All cases explicitly use **G1**: reduce abandoned eligible failed-payment attempts
divided by eligible failed-payment attempts in observation window ticks 0–20.
With no eligible attempts the rate is undefined, not zero. Duplicate effects,
retry cost, latency and audit coverage are separate; they are not a combined
fitness score. World/event/detection/availability times are distinct even when
equal in a fixture. W grants for deployment are separate from D selection grants.

## T1 — Inferred choice with green verification

| Required distinction | Authored state |
| --- | --- |
| Goal | G1; duplicate effects tracked separately even if abandonment falls. |
| Belief | Jin's B1: a fresh key per retry avoids collisions; high stated confidence, no interface rationale. |
| World | World A: first execution succeeds but acknowledgment is lost; retry with a new key can execute the payment twice. |
| Choice | D1 `idempotency`: {stable operation key, new key each attempt, unspecified}; v1 selects new key. |
| Authority | Jin has no idempotency grant. Ada has scoped interface authority; Elena has deployment authority. None implies world truth. |
| Accessible knowledge | Jin holds thin Work Item WI1 and repository conventions, not Ada's K-interface@1. Missing interface rationale is recorded at selection. Private audit retains K-interface@1. |
| Evidence | Initially none about interface safety. V1 tests conformance to B1; later O1 independently observes duplicate execution for deployment DEP1. |
| Revision | After O1 and Ada's delivered contract, B2 retracts B1; D1 v2 selects stable key under Ada's explicit authorization. DEP1 still pins v1. |
| Actor / Role / Function | Jin: human / developer / implementer. Ada: human / architect / interface steward. Elena: human / reliability lead / feedback observer. O owns these assignments; K owns their holdings. No role implies another function or grant. |
| Ownership | D owns D1; W WI1/proposal/DEP1; A V1; L duplicate outcome/O1/B2; K contract delivery; O authorization; G G1. |

| Fact | Tick | Owner / candidate event and resulting state | Earlier typed parents |
| --- | --- | --- | --- |
| T1.0 | 0 | Initialize the state above, including fixed workload and grants | none |
| T1.1 | 1 | D `DecisionSelected`: D1@1=new key, inferred authority, evidence absent; record missing interface rationale | d:T1.0 |
| T1.2 | 2 | W `ChangeProposalCreated`: CP1 pins D1@1 | d:T1.1 |
| T1.3 | 3 | A `VerificationCompleted`: V1 passes new-key spec on CP1; validation unknown | d:T1.2; s:T1.1 |
| T1.4 | 4 | W `DeploymentCompleted`: Elena ships CP1 as DEP1 under her separate grant | d:T1.2; s:T1.3,T1.0 |
| T1.5 | 5 | L `WorldOutcomeOccurred`: workload acknowledgment loss + DEP1 cause duplicate effect, still private | d:T1.4,T1.0 |
| T1.6 | 7 | L `OutcomeObserved`: O1 detects T1.5, available to Elena at 7 | d:T1.5 |
| T1.7 | 8 | K `KnowledgeTransferred`: Elena's O1 delivered to Jin; original subject DEP1 retained | d:T1.6 |
| T1.8 | 9 | K `KnowledgeTransferred`: Ada's K-interface@1 delivered to Jin | d:T1.0; a:T1.7 |
| T1.9 | 10 | L `BeliefRevised`: Jin B1 -> B2 retracts fresh-key rationale | d:T1.7,T1.8; s:T1.6 |
| T1.10 | 11 | O `DecisionAuthorized`: Ada authorizes stable-key selection within her initial scope | d:T1.0; a:T1.9 |
| T1.11 | 12 | D `DecisionRevised`: D1@2=stable key, cites B2, grant and sources; no automatic redeploy | d:T1.1,T1.9,T1.10; s:T1.6,T1.8 |

**Backward walk:** D1@2 requires both the delivered sources and authorization;
authorization alone could not establish B2. O1 concerns DEP1, whose CP1 pins D1@1;
the duplicate follows deployed new-key behavior plus acknowledgment-loss exposure,
not Jin's lack of authority. V1 leads back to B1's spec, so it cannot independently
confirm B1. Before T1.7/8 Jin cannot use O1 or Ada's contract.

**Counterprobes/results:** remove acknowledgment-loss exposure and the duplicate
does not follow; remove delivery and the proposed informed revision is invalid.
Relabel Jin as an agent with identical state and the trace is unchanged by design.
Reject `verified => validated`, audit-as-access, and assumption-as-damage rules
(I2/I4/I5/I6). These are manual consistency findings, not executed metamorphic tests.

## T2 — Legitimate delegation without world evidence

| Required distinction | Authored state |
| --- | --- |
| Goal | G1, unchanged by delegation. |
| Belief | Agent implementer a1 has B1: one retry might reduce abandonment; support unknown. |
| World | Could be A or B; no traffic or outcome observation occurs in this trace. Actual recovery remains unknown to a1. |
| Choice | D2 `retry_count`: {none, one, three}; v1 selects one. |
| Authority | Maya's explicit initial grant permits delegating counts {none, one} for WI2. She grants a1 that discretion; no shipping authority is granted. |
| Accessible knowledge | a1 holds WI2, alternatives and the delivered delegation record. It has no Leo workload study or outcome samples. |
| Evidence | Delegation is evidence of permission only. Support for the proposition “one retry improves G1” stays absent. |
| Revision | Maya later revokes discretion because the assigned work scope ends, with no new world evidence. D2@2 retains one but records no current grant; D2@1 was legitimately selected. B1 is unchanged. |
| Actor / Role / Function | Maya: human / product lead / trade-off owner, with explicit delegable grant. a1: agent / assigned developer / implementer. Assignment, grant, holding and function are separate O/K records. |
| Ownership | O owns grant/revocation, D choice/justification versions, K accessible grant record, L B1, G G1; W has no deployment. |

| Fact | Tick | Owner / candidate event and resulting state | Earlier typed parents |
| --- | --- | --- | --- |
| T2.0 | 0 | Initialize G1, actors, WI2, B1 and Maya's scoped grant | none |
| T2.1 | 1 | O `DecisionDelegated`: grant GD2 to a1 for WI2 counts none/one | d:T2.0 |
| T2.2 | 2 | K `KnowledgeTransferred`: delegation record becomes usable by a1 | d:T2.1 |
| T2.3 | 3 | D `DecisionSelected`: D2@1=one; GD2 valid, world support absent | d:T2.2; s:T2.1 |
| T2.4 | 4 | O `AuthorityRevoked`: Maya ends GD2 for subsequent actions | d:T2.1 |
| T2.5 | 5 | K `KnowledgeTransferred`: revocation notice reaches a1 | d:T2.4 |
| T2.6 | 6 | D `DecisionRevised`: D2@2 same choice, current authority absent; no belief/evidence improvement | d:T2.3,T2.5; s:T2.4 |

**Backward walk:** D2@2 references the revocation, not a payment observation;
D2@1 still points to GD2 while valid at tick 3. GD2 traces to Maya's delegable
scope, not her role name. Selection follows receipt of discretion, with no source
about recovery. No `BeliefRevised` or outcome fact can be inferred anywhere.

**Counterprobes/results:** claiming delegated count three fails the scope check,
although three is a domain alternative; an explicitly unsupported selection is
a different permitted modeling path, never silently labeled delegated. Count four
fails alternative membership entirely. A new authorized action using GD2 after
tick 4 fails even before its notice arrives; a1's belief about permission can be
stale. Replacing a1's kind with human changes none of these conclusions. A status
enum with mutually exclusive `delegated`/`unsupported` cannot express this case
(I1/I2/I3/I8). No empirical uncertainty reduction follows from closure.

## T3 — Wrong authorized policy

| Required distinction | Authored state |
| --- | --- |
| Goal | G1, with unchanged eligible soft-decline class and window across the comparison. |
| Belief | Maya's B1: blanket non-retry of declines best serves G1. This factual claim is separate from enacted P1. |
| World | World B contains a soft-decline class that can recover on a delayed retry. Blanket non-retry can lose a completion opportunity. This is a fixture, not real payment guidance. |
| Choice | D3 `declined_handling`: {do not retry, selected soft declines, all}; v1 selects do not retry to conform to P1. |
| Authority | Maya has authored scope to enact P1 and approve bounded evaluation exceptions; Elena separately may deploy. P1 is legitimate despite its weak rationale. |
| Accessible knowledge | Maya/Jin hold P1. Sarah holds historical rationale and scope tacitly; it is not copied by P1's availability. Leo can receive independent evaluation observations. |
| Evidence | Initially no current fitness evidence. A bounded evaluation compares P1 behavior with selected-soft behavior on matched authored workloads; observation O3 reports abandonment under baseline and recovery under trial. |
| Revision | Leo/Maya revise B1; Maya enacts P2 permitting selected soft declines. D3@2 chooses that option. Earlier CP3/DEP3 and their assessments remain pinned to P1/D3@1. |
| Actor / Role / Function | Maya: product lead / policy and trade-off owner; Jin: developer / implementer; Leo: analyst / validation interpreter; Elena: reliability lead / deployment and feedback operator; Sarah: senior engineer / historian. All are human here; functions/grants/holdings remain distinct. |
| Ownership | G owns G1/P1/P2; O grants/exception; W baseline and evaluation deployments; L outcomes/O3/B2; A conformance and fitness assessments; K delivery; D D3. |

| Fact | Tick | Owner / candidate event and resulting state | Earlier typed parents |
| --- | --- | --- | --- |
| T3.0 | 0 | Initialize state and bounded evaluation protocol with fixed baseline/trial workload refs | none |
| T3.1 | 1 | D `DecisionSelected`: D3@1=no declines under P1; world support absent | d:T3.0 |
| T3.2 | 2 | W `ChangeProposalCreated`: CP3 implements D3@1 | d:T3.1 |
| T3.3 | 3 | A `VerificationCompleted`: CP3 conforms to P1; fitness unknown | d:T3.2; s:T3.1 |
| T3.4 | 4 | W `DeploymentCompleted`: Elena installs CP3 as baseline DEP3 | d:T3.2; s:T3.3,T3.0 |
| T3.5 | 5 | O `DecisionAuthorized`: Maya grants evaluation-only exception to P1 for selected-soft trial | d:T3.0 |
| T3.6 | 6 | D `DecisionSelected`: evaluation D3-trial@1=selected soft declines, exception scope retained | d:T3.5 |
| T3.7 | 7 | W `ChangeProposalCreated`: CP3-trial pins D3-trial@1 for evaluation | d:T3.6 |
| T3.8 | 8 | W `DeploymentCompleted`: Elena runs CP3-trial only in authorized evaluation | d:T3.7; s:T3.5,T3.0 |
| T3.9 | 9 | L `WorldOutcomeOccurred`: matched baseline/trial exposures yield abandonment/recovery respectively | d:T3.4,T3.8,T3.0 |
| T3.10 | 11 | L `OutcomeObserved`: O3 detects results at 11, available to Leo at 11; subjects retain both deployments | d:T3.9 |
| T3.11 | 12 | A `AssessmentRecorded`: Leo's limited fitness assessment challenges B1, not P1's authorization | d:T3.10; s:T3.0 |
| T3.12 | 13 | K `KnowledgeTransferred`: O3 and assessment reach Maya | d:T3.10,T3.11 |
| T3.13 | 14 | L `BeliefRevised`: Maya B1 -> B2 narrows claim to sampled soft class | d:T3.12; s:T3.10,T3.11 |
| T3.14 | 15 | G `PolicyRevised`: Maya enacts P2 under original policy authority | d:T3.13; s:T3.0 |
| T3.15 | 16 | D `DecisionRevised`: D3@2=selected soft declines under P2; no automatic deployment change | d:T3.1,T3.14; s:T3.10,T3.11 |

**Backward walk:** D3@2 needs enacted P2, which follows a scoped belief revision
using delivered observations. O3 traces to both behavior variants and workload,
not a new policy declaring itself true. Trial deployment traces to an explicit
exception: omitting T3.5 would make the purported authorized trial contradictory.
The baseline conforms to P1 even though its authored outcome is worse for G1.
Changing P2 cannot relabel old DEP3 outcomes or retroactively fail conformance.

**Counterprobes/results:** replace the World with hard declines that never recover
and O3 no longer supports P2. Remove matched eligibility and the comparison is
insufficient. If O3 arrives after another revision, retain its old subject refs.
Reject `authorized => fit`, automatic policy revision on observation, and silent
redeployment (I1/I2/I5/I7). Statistical generality, trial safety and performance
are unproven; this manual two-behavior fixture only exposes the required separation.

## T4 — Conflicting sources with shared dependencies

| Required distinction | Authored state |
| --- | --- |
| Goal | G1; duplicate effects are still a separate constraint/measure. |
| Belief | Ada B1: the provider deduplicates even new retry keys; uncertainty initially understated. |
| World | World A can duplicate under new keys. Actors do not see that rule; the supplied observations can also be incomplete. |
| Choice | D4 `idempotency`: {stable operation key, new key each attempt, unspecified}; v1 new key, later v2 stable key as a precaution, not a claim that conflict is solved. |
| Authority | Ada has explicit authority for both options. No source majority grants or removes that authority. |
| Accessible knowledge | Ada holds R1 and R2, both copied from vendor note S0. Noah owns independently collected trace S1 suggesting duplicates; Ada cannot use it until delivery. |
| Evidence | R1/R2 support B1 with shared origin S0; S1 challenges B1 with a separate method. Quality/applicability remain uncertain; counting reports as independent votes is invalid. |
| Revision | After S1 delivery, B2 retains conflict and reduces claimed confidence; D4@2 chooses stable key as reversible caution with the conflict still recorded. |
| Actor / Role / Function | Ada: human / architect / interface steward. Noah: human / assurance analyst / source-lineage assessor. Elena: human / reliability lead / collector of the underlying trace. Role titles neither establish independence nor grant Ada access to S1. |
| Ownership | K owns source items/copies/access; L owns underlying observations/B2; A owns Noah's source assessment; O Ada's grant; D D4; G G1. No deployment/outcome is claimed here. |

| Fact | Tick | Owner / candidate event and resulting state | Earlier typed parents |
| --- | --- | --- | --- |
| T4.0 | 0 | Initialize G1, grant, accessible R1/R2->S0, inaccessible S1 and its observation lineage | none |
| T4.1 | 1 | D `DecisionSelected`: D4@1=new key, authorized; cites R1/R2 and shared origin, no independent confirmation | d:T4.0; s:T4.0 |
| T4.2 | 2 | K `KnowledgeTransferred`: S1 reaches Ada from Noah, preserving original observation refs | d:T4.0 |
| T4.3 | 3 | A `AssessmentRecorded`: Noah records S0 dependence of R1/R2 and conflict with S1; available to Noah | d:T4.0; a:T4.2 |
| T4.4 | 4 | K `KnowledgeTransferred`: assessment reaches Ada | d:T4.3 |
| T4.5 | 5 | L `BeliefRevised`: Ada B1 -> B2, conflict explicit; no truth oracle or majority vote | d:T4.2,T4.4; s:T4.0,T4.3 |
| T4.6 | 6 | D `DecisionRevised`: D4@2=stable key, authorized precaution; evidence still conflicted | d:T4.1,T4.5; s:T4.3 |

**Backward walk:** D4@2 reflects precaution under B2, not a finding that S1 is
infallible. B2 requires actual receipt of S1 and the assessment. Following R1 and
R2 backward reaches one origin S0; following S1 reaches a distinct observation
method with its own uncertainty. The fixture's private World rule supplies no
missing evidence. No outcome can be inferred from this unshipped selection.

**Counterprobes/results:** add ten more copies of S0 and independent support is
unchanged. Remove T4.2 and Ada cannot incorporate S1. Rename sources/actors while
preserving dependencies and conflict remains. A newer timestamp alone cannot
resolve contradictory scopes. Reject evidence-as-a-single-owned-blob in D and
majority-by-report-count (I4/I5); contested independence stays open for AE-013.

## T5 — Harmless unsupported choice

| Required distinction | Authored state |
| --- | --- |
| Goal | G1; retry cost and latency assessed over the same window, no claim beyond it. |
| Belief | Jin B1: three retries are preferable to one; unsupported rather than known false. |
| World | Benign World A subset: every exposed transient failure recovers on the first delayed retry. Both caps execute identical behavior in this window. |
| Choice | D5 `retry_count`: {none, one, three}; v1 selects three. |
| Authority | Jin lacks a retry-count grant; Elena has separate shipping authority. Unsupported selection is recorded, not secretly legitimized by success. |
| Accessible knowledge | Jin holds WI5 and repository defaults only; Leo's broader workload evidence is absent. Later a bounded monitoring summary is delivered. |
| Evidence | No support for three over one initially. The window summary finds no duplicate effect and no execution beyond the first retry; it cannot discriminate the two caps. |
| Revision | B2 narrows to “no harm observed on this first-retry-only workload.” D5@2 retains three and missing authority; justification gains a limited observation, not validation of superiority. |
| Actor / Role / Function | Jin: human / developer / implementer. Elena: human / reliability lead / shipping and monitoring operator. O owns roles/functions/grants; K separately controls evidence access. |
| Ownership | D owns D5, W proposal/deployment, L outcomes/summary/B2, K delivery, A bounded assessment, O grants, G G1. |

| Fact | Tick | Owner / candidate event and resulting state | Earlier typed parents |
| --- | --- | --- | --- |
| T5.0 | 0 | Initialize state and fixed first-retry recovery workload | none |
| T5.1 | 1 | D `DecisionSelected`: D5@1=three; no authority, no comparative evidence | d:T5.0 |
| T5.2 | 2 | W `ChangeProposalCreated`: CP5 pins D5@1 | d:T5.1 |
| T5.3 | 3 | A `VerificationCompleted`: CP5 implements chosen cap; fitness unknown | d:T5.2; s:T5.1 |
| T5.4 | 4 | W `DeploymentCompleted`: Elena ships CP5 under separate grant | d:T5.2; s:T5.3,T5.0 |
| T5.5 | 5 | L `WorldOutcomeOccurred`: eligible payments recover on first retry, no duplicate effect | d:T5.4,T5.0 |
| T5.6 | 20 | L `OutcomeObserved`: monitoring window closes, summary available to Elena at 20 | d:T5.5 |
| T5.7 | 21 | K `KnowledgeTransferred`: window summary reaches Jin | d:T5.6 |
| T5.8 | 22 | A `AssessmentRecorded`: summary cannot distinguish caps one/three; available to Jin as assessor | d:T5.7; s:T5.6 |
| T5.9 | 23 | L `BeliefRevised`: Jin B1 -> B2 limits claim to observed exposure | d:T5.8; s:T5.6 |
| T5.10 | 24 | D `DecisionRevised`: D5@2=three; missing grant remains; observation refs added | d:T5.1,T5.9; s:T5.6,T5.8 |

**Backward walk:** D5@2's new justification leads to one limited window, not
evidence favoring three over one. Successful outcomes trace to first-retry
recovery plus deployed behavior. No event obtains a grant, so success cannot
repair authority. Work after window 20 and future failure classes are unobserved.

**Counterprobes/results:** replace cap three with one on identical exposures and
executed retries/outcomes remain identical. With no traffic there is no transaction
incident and G1 is undefined. With repeated failures beyond the first retry, the
equivalence no longer follows. A clarification step could add delay without
improving this window's outcomes; its numerical cost is unmodeled. Reject automatic
assumption penalties and `no incident => validated` (I2/I6/I7).

## Cross-case audit and disposition

| Challenged design | Concrete contradiction | Tabletop disposition |
| --- | --- | --- |
| One resolved/delegated/evidenced/correct enum | T2 is both delegated and lacking world evidence; T3 conformant but unfit for sampled class | Reject combined enum; keep independent axes (I2). |
| Decision owns grants, sources, observations and beliefs | T2 revocation and T4 source delivery would require mutating multiple Decision-owned copies of the same external fact | Prefer versioned references and separate lifecycle owners; heavy aggregate not justified by these cases. |
| Belief revision and policy enactment are one mutation | T3 evidence may challenge B1 while P1 remains active pending authorized enactment | L owns belief revision, G policy enactment; D/W pin versions (I1/I7). |
| Role replacement copies function/holdings/authority | Giving a1 a developer role cannot supply Maya's grant or Sarah's tacit rationale | Separate O assignments/grants and K holdings; no implicit transfer (I3/I8). |
| Private audit is usable knowledge | T1 Jin could know Ada's contract before T1.8; T4 Ada could use S1 before delivery | Keep content and access distinct (I4). |
| Agreement/verification is independent validation | T1 tests are generated from B1; T4 reports share S0 | Preserve subject and source/method dependencies (I5). |
| Missing justification predicts harm | T5 cap differences are not exposed; T1 harm also needs acknowledgment loss | World consumes behavior/exposure only (I6). |
| Latest version rewrites history | T3 P2 would change the meaning of earlier deployment results | Pin subjects and append revisions, keep prior parents (I1/I9). |

Manual audit found no remaining contradiction in these five revised sketches:
every referenced parent precedes the fact, each revision has a prior version and
named owner, and every actor evidence use follows a holding or delivery. The
initial policy-trial sketch required an explicit evaluation exception; T3.5–8
retain that correction. T4 required delivery of the assessment, not only S1;
T4.4 records it. These are substantive drafting corrections, not automated tests.

**Disposition: pass for the bounded AE-002 documentation/tabletop task.** Reject
the combined status and heavy ownership proposal; propose a small versioned
Decision model with independent authority/support. No mechanism is implemented.
Evidence ownership across L/A/K/D, authority conflicts, atomicity, source-quality
rules and player discoverability remain open with named revisit activities in
the domain model. Five authored cases cannot establish universal coverage,
empirical calibration, executable correctness, participant comprehension or
architecture acceptance. AE-003 is a recommendation only after this delivery
is available and reviewed; no successor is executed here.
