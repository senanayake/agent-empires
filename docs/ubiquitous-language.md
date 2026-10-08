# PaymentCo language after the AE-002 tabletop

Proposed vocabulary, 2026-10-08. The [five authored cases](../research/experiments/AE-002/tabletop.md)
challenge the [campaign model](mvp-campaign.md#5-core-ddd-model); they are not
participant observations or empirical payment advice. Ownership is defined in
[the domain model](domain-model.md) and [context map](context-map.md).

| Term | Meaning and boundary |
| --- | --- |
| Intent | Desired change: help customers finish payment. It is not a measurable result. |
| Goal | Versioned measure, eligible population, direction and observation window. PaymentCo seeks lower failed-payment abandonment; duplicate charges, retry cost, latency and audit coverage remain separate measures. |
| Belief | An actor's or explicitly identified group's current proposition about the world, with source and confidence. Confident belief can be wrong; the organization has no automatic shared mind. |
| Policy | A versioned normative instruction with scope and recognized authority. Its factual rationale is a separate belief; conformance does not establish outcome fitness. |
| World | Private simulation rules and workload producing consequences from deployed behavior. Its state is not actor knowledge, a true requirement, or a correctness flag. |
| Decision | A named question with alternatives and an append-only sequence of choice/justification versions. Selection closes the question operationally; justification may remain weak. |
| Choice / resolution | Unselected or selected alternative in a particular decision version. A new version can change justification while keeping the same choice. |
| Authority | Recognized permission for an actor to take a scoped action under specified constraints and effective times. A role label, source's authority claim, and useful knowledge are not grants. |
| Delegation | An explicit grant from a recognized grantor to a recipient within the grantor's delegable scope. Transfers discretion, not information about the world. |
| Evidence | A versioned observation or assessment offered in support of or against a particular proposition. It has a method, subject, source dependencies and scope. A policy document evidences what the policy says, not whether it improves payment outcomes. |
| Evidence support | A relationship to a proposition: absent, supporting, challenging, conflicting or insufficient as appropriate. These are qualitative summaries with reasons, not a universal ordered score or an authority status. |
| Assumption | A consequential choice with insufficient authority or evidential support for its claimed justification. Record the specific gap; delegated but unvalidated and unauthorized but successful are different cases. |
| Provenance | Versioned origin/justification references, including unavailable information recorded at choice time. A source citation is not access to the source, source independence, or a direct causal edge. |
| KnowledgeItem | Versioned informational content with topic, source, freshness and explicit/tacit form; may be false. It does not itself establish who can use it. |
| KnowledgeHolding | A holder's usable access to a specific item/version. Archived content can survive while all usable organizational holdings are lost. |
| Actor | An acting human or agent with capabilities, availability and identity. Kind alone confers neither authority nor correctness. |
| Role | A formal assignment of responsibilities. Reassigning Engineering developer does not transfer grants or historical rationale. |
| OrganizationalFunction | Work relied on, such as incident historian, translator or feedback observer; coverage can be informal, shared or absent. Assignment is not proof of performance. |
| Channel | A transfer path with endpoints and modeled delay/capacity/reliability. Sending does not grant recipient access; successful delivery may create a holding. |
| Work Item | A request, possibly thin, linked to intent/goal and needed decisions; not an implicit copy of organizational knowledge. |
| Change Proposal / deployment | Proposed behavior pinned to decision versions / installed behavior pinned to that proposal. New decisions do not silently change old deployments. |
| Verification | Assessment of implementation against a specified interpretation. Tests generated from that interpretation can verify it without independently validating it. |
| Validation | Assessment of interpretation or behavior against explicit goal/world observations, with scope and limitations. It can challenge an authorized policy. |
| Outcome / observation | World consequence / a partial record made available later through an observation method. No observation does not mean no harm, and no exposure does not prove fitness. |
| Learning / revision | An explicit change to a belief, choice, policy or goal with a reason and prior version. Evidence can leave a choice unchanged; selection alone creates no justified information gain. |

Do not introduce a combined status such as `inferred -> delegated -> evidenced ->
correct`. T2 requires selected + delegated + no world evidence simultaneously;
T3 requires authorized + conformant + poor fitness; T5 requires unsupported +
harmless in its tested window. Confidence, authority, support and assurance
dimensions must remain separately inspectable. Numerical entropy is deferred.
