"""Versioned choices, scoped authority and declared evidence, without world truth.

These are trusted single-consumer simulation owners sharing one KnowledgeStore
and EventHistory. Root grants and evidence assessments are authored/imported by
trusted setup/assurance code, not authenticated here. Actor policy receives only
a fresh public knowledge view. Source IDs denote declared ultimate dependencies;
new report IDs never establish independence. No probability update is implied.
"""

from dataclasses import asdict, dataclass, replace
import json

from .actors import require_text
from .clock import require_tick
from .events import CausalLink, EntityRef, Event, EventHistory
from .knowledge import ActorKnowledge, KnowledgeStore, KnownProposition


CONFIDENCE = ("unknown", "low", "medium", "high")


def _strings(values: tuple[str, ...], name: str, *, nonempty: bool = False) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be an immutable tuple")
    for value in values:
        require_text(value, name)
    if len(set(values)) != len(values) or (nonempty and not values):
        raise ValueError(f"{name} must contain unique values and cannot be empty here")


def _confidence(value: str) -> None:
    if value not in CONFIDENCE:
        raise ValueError("confidence must be categorical")


def _present(store: KnowledgeStore, history: EventHistory, actor_id: str) -> ActorKnowledge:
    view = store.view_for(actor_id)
    if any(e.event_type == "ActorDeparted" and e.payload["actor_id"] == actor_id
           for e in history.events):
        raise ValueError("actor has departed")
    return view


def _payload(value) -> dict:
    # Dataclasses contain immutable tuples; event JSON explicitly contains lists.
    return json.loads(json.dumps(asdict(value)))


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    grant_id: str
    actor_id: str
    scope: str
    options: tuple[str, ...]
    action: str = "select"
    valid_from: int = 0
    valid_until: int | None = None
    can_delegate: bool = False
    basis: str = "explicit_authorization"
    parent_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("grant_id", "actor_id", "scope", "action"):
            require_text(getattr(self, name), name)
        _strings(self.options, "options", nonempty=True)
        require_tick(self.valid_from)
        if self.valid_until is not None:
            require_tick(self.valid_until)
            if self.valid_until <= self.valid_from:
                raise ValueError("authority validity interval must be nonempty")
        if type(self.can_delegate) is not bool:
            raise TypeError("can_delegate must be boolean")
        if self.basis not in ("explicit_authorization", "policy_constraint", "delegated_discretion"):
            raise ValueError("unknown authority basis")
        if self.parent_id is not None:
            require_text(self.parent_id, "parent_id")
        if (self.parent_id is None) != (self.basis != "delegated_discretion"):
            raise ValueError("delegated authority must name its parent")

    @property
    def ref(self) -> EntityRef:
        return EntityRef("authority_grant", self.grant_id, 1)


class AuthorityRegistry:
    """Separate grant lifecycle owner; selection never creates a grant.

    add_root/revoke are trusted organizational lifecycle inputs. delegate checks
    the issuing actor against a currently valid delegable parent. Child scope,
    action and expiry are inherited, options can only narrow. A revoked ancestor
    invalidates future use without changing any historical decision version.
    """

    def __init__(self, store: KnowledgeStore, history: EventHistory) -> None:
        self._store, self._history = store, history
        self._grants: dict[str, tuple[AuthorityGrant, Event]] = {}
        self._revoked: dict[str, Event] = {}

    def _record(self, grant: AuthorityGrant, event_type: str, *, tick: int,
                command_id: str, correlation_id: str, parents=()) -> Event:
        if grant.grant_id in self._grants:
            raise ValueError("duplicate authority grant")
        _present(self._store, self._history, grant.actor_id)
        if grant.valid_until is not None and tick >= grant.valid_until:
            raise ValueError("authority already expired")
        event = self._history.append(
            tick=tick, event_type=event_type, command_id=command_id,
            correlation_id=correlation_id, entities=(grant.ref,), parents=parents,
            payload={"grant": _payload(grant)},
        )
        self._grants[grant.grant_id] = grant, event
        return event

    def add_root(self, grant: AuthorityGrant, *, tick: int, command_id: str,
                 correlation_id: str) -> Event:
        if type(grant) is not AuthorityGrant or grant.parent_id is not None:
            raise ValueError("root authority must be a non-delegated AuthorityGrant")
        return self._record(grant, "AuthorityGranted", tick=tick,
                            command_id=command_id, correlation_id=correlation_id)

    def _chain(self, grant_id: str, tick: int) -> tuple[tuple[AuthorityGrant, Event], ...]:
        require_tick(tick)
        if grant_id not in self._grants:
            raise ValueError("unknown authority grant")
        grant, event = self._grants[grant_id]
        if (grant_id in self._revoked or tick < max(event.tick, grant.valid_from)
                or (grant.valid_until is not None and tick >= grant.valid_until)):
            raise ValueError("authority revoked, not yet valid or expired")
        _present(self._store, self._history, grant.actor_id)
        ancestors = self._chain(grant.parent_id, tick) if grant.parent_id else ()
        return ((grant, event),) + ancestors

    def evaluate(self, grant_id: str, actor_id: str, scope: str, option: str,
                 *, tick: int, action: str = "select") -> tuple[AuthorityGrant, tuple[CausalLink, ...]]:
        chain = self._chain(grant_id, tick)
        grant = chain[0][0]
        if (grant.actor_id != actor_id or grant.scope != scope or grant.action != action
                or option not in grant.options):
            raise ValueError("authority does not cover actor, action, scope or option")
        return grant, tuple(CausalLink(e.event_id, "supporting_evidence") for _, e in chain)

    def delegate(self, grant_id: str, parent_id: str, grantor_id: str, actor_id: str,
                 *, options: tuple[str, ...], tick: int, command_id: str,
                 correlation_id: str, can_delegate: bool = False) -> Event:
        _strings(options, "options", nonempty=True)
        chain = self._chain(parent_id, tick)
        parent = chain[0][0]
        if (parent.actor_id != grantor_id or not parent.can_delegate
                or not set(options) <= set(parent.options)):
            raise ValueError("authority cannot be delegated by this actor or beyond its scope")
        grant = AuthorityGrant(grant_id, actor_id, parent.scope, options, parent.action,
                               tick, parent.valid_until, can_delegate,
                               "delegated_discretion", parent_id)
        return self._record(grant, "DecisionDelegated", tick=tick, command_id=command_id,
                            correlation_id=correlation_id,
                            parents=tuple(CausalLink(e.event_id, "direct_cause") for _, e in chain))

    def revoke(self, grant_id: str, *, tick: int, command_id: str, correlation_id: str) -> Event:
        if grant_id not in self._grants or grant_id in self._revoked:
            raise ValueError("unknown or already revoked authority")
        grant, issued = self._grants[grant_id]
        event = self._history.append(
            tick=tick, event_type="AuthorityRevoked", command_id=command_id,
            correlation_id=correlation_id, entities=(EntityRef("authority_grant", grant_id, 2),),
            parents=(CausalLink(issued.event_id, "direct_cause"),),
            payload={"grant_id": grant_id, "issued_version": grant.ref.as_dict()},
        )
        self._revoked[grant_id] = event
        return event

    def context_links(self, actor_id: str, scope: str) -> tuple[CausalLink, ...]:
        """Keep known revocations in an explicitly unsupported revision's audit."""
        ids = set()
        for grant, _ in self._grants.values():
            if grant.actor_id == actor_id and grant.scope == scope:
                current = grant
                ids.add(current.grant_id)
                while current.parent_id:
                    ids.add(current.parent_id)
                    current = self._grants[current.parent_id][0]
        return tuple(CausalLink(e.event_id, "association") for key, e in self._revoked.items() if key in ids)


@dataclass(frozen=True, slots=True)
class DecisionQuestion:
    decision_id: str
    topic: str
    scope: str
    alternatives: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("decision_id", "topic", "scope"):
            require_text(getattr(self, name), name)
        _strings(self.alternatives, "alternatives", nonempty=True)

    @property
    def ref(self) -> EntityRef:
        return EntityRef("decision_question", self.decision_id, 1)


@dataclass(frozen=True, slots=True)
class CapabilityProfile:
    """Toy deterministic policy settings shared by all actor kinds.

    Prefer an accessible exact option claim if read_claims, otherwise use the
    declared option order. Conflicts use that same order, never report majority.
    Confidence is stated, not computed from evidence or calibrated accuracy.
    """

    preference: tuple[str, ...]
    can_infer: bool = True
    read_claims: bool = True
    confidence: str = "unknown"

    def __post_init__(self) -> None:
        _strings(self.preference, "preference", nonempty=True)
        _confidence(self.confidence)
        if type(self.can_infer) is not bool or type(self.read_claims) is not bool:
            raise TypeError("capabilities must be booleans")

    def propose(self, question: DecisionQuestion, view: ActorKnowledge) -> tuple[str, tuple[str, ...]]:
        if not self.can_infer:
            raise ValueError("profile cannot infer")
        if set(self.preference) != set(question.alternatives):
            raise ValueError("preference must rank exactly the question alternatives")
        entries = tuple(e for e in view.entries if self.read_claims and e.item.topic == question.topic
                        and e.item.proposition in question.alternatives)
        claims = {e.item.proposition for e in entries}
        selected = next((v for v in self.preference if v in claims), self.preference[0])
        return selected, tuple(e.holding.holding_id for e in entries)


@dataclass(frozen=True, slots=True)
class EvidenceUse:
    """A trusted assessment of a currently accessible holding's content.

    subject pins this question or an existing version of this decision. Declared
    ultimate source roots come only from the holding; no lookup follows a root.
    verification can support conformance elsewhere, never world fitness here.
    """

    holding_id: str
    subject: EntityRef
    option: str
    stance: str
    method: str
    quality: str

    def __post_init__(self) -> None:
        require_text(self.holding_id, "holding_id")
        require_text(self.option, "option")
        if type(self.subject) is not EntityRef:
            raise TypeError("subject must be a version reference")
        if self.stance not in ("supports", "challenges", "inconclusive"):
            raise ValueError("unknown evidence stance")
        if self.method not in ("verification", "observation", "report"):
            raise ValueError("unknown evidence method")
        if self.quality not in ("weak", "usable"):
            raise ValueError("unknown evidence quality")


@dataclass(frozen=True, slots=True)
class EvidenceFinding:
    assessment: EvidenceUse
    item: EntityRef
    holding: EntityRef
    source_ids: tuple[str, ...]
    eligible: bool
    exclusion: str | None


@dataclass(frozen=True, slots=True)
class DecisionVersion:
    decision_id: str
    version: int
    prior: EntityRef | None
    actor_id: str
    selected: str
    confidence: str
    authority_basis: str
    grant_ref: EntityRef | None
    support: str
    evidence: tuple[EvidenceFinding, ...]
    source_ids: tuple[str, ...]
    backed_source_ids: tuple[str, ...]
    rationale: tuple[EntityRef, ...]
    missing_information: tuple[str, ...]
    reason: str
    event_id: str

    @property
    def ref(self) -> EntityRef:
        return EntityRef("decision", self.decision_id, self.version)


class Decisions:
    """Local choice consistency boundary; no observations, grants or learning created.

    Question identity/scope/alternatives stay fixed in this bounded API. Revisions
    append choices/justifications with an expected-version guard. Alternative-set
    or scope revisions need a new question; richer revision semantics are deferred.
    """

    def __init__(self, store: KnowledgeStore, authority: AuthorityRegistry, history: EventHistory) -> None:
        self._store, self._authority, self._history = store, authority, history
        self._questions: dict[str, DecisionQuestion] = {}
        self._versions: dict[str, tuple[DecisionVersion, ...]] = {}

    def register(self, question: DecisionQuestion) -> None:
        if type(question) is not DecisionQuestion:
            raise TypeError("expected DecisionQuestion")
        if question.decision_id in self._questions:
            raise ValueError("duplicate decision question")
        self._questions[question.decision_id] = question
        self._versions[question.decision_id] = ()

    def versions(self, decision_id: str) -> tuple[DecisionVersion, ...]:
        if decision_id not in self._versions:
            raise ValueError("unknown decision")
        return self._versions[decision_id]

    def version(self, decision_id: str, version: int) -> DecisionVersion:
        values = self.versions(decision_id)
        if type(version) is not int or not 1 <= version <= len(values):
            raise ValueError("unknown decision version")
        return values[version - 1]

    def _lineage(self, entry: KnownProposition) -> tuple[CausalLink, ...]:
        # Same acquisition/access distinction as AE-005: transfer carries any
        # distortion; a later access restoration must never replace that origin.
        acquisition = next(e for e in reversed(self._history.events)
                           if e.event_type in ("KnowledgeTransferred", "KnowledgeHoldingRecorded")
                           and any(r.entity_type == "knowledge_holding"
                                   and r.entity_id == entry.holding.holding_id for r in e.entities))
        access = next(e for e in reversed(self._history.events)
                      if e.event_type in ("KnowledgeHoldingRecorded", "HoldingAccessChanged")
                      and entry.holding.ref in e.entities)
        return tuple(dict.fromkeys(CausalLink(e.event_id, "supporting_evidence")
                                   for e in (acquisition, access)))

    def infer(self, decision_id: str, actor_id: str, profile: CapabilityProfile, *,
              expected_version: int, tick: int, command_id: str, correlation_id: str,
              missing_information: tuple[str, ...] = ()) -> DecisionVersion:
        self.versions(decision_id)
        if type(profile) is not CapabilityProfile:
            raise TypeError("expected CapabilityProfile")
        view = _present(self._store, self._history, actor_id)
        option, rationale = profile.propose(self._questions[decision_id], view)
        return self.select(decision_id, option, actor_id=actor_id, expected_version=expected_version,
                           tick=tick, command_id=command_id, correlation_id=correlation_id,
                           confidence=profile.confidence, rationale_holding_ids=rationale,
                           reason="capability preference over available exact claims",
                           missing_information=missing_information)

    def select(self, decision_id: str, option: str, *, actor_id: str, expected_version: int,
               tick: int, command_id: str, correlation_id: str, confidence: str = "unknown",
               reason: str, grant_id: str | None = None, evidence: tuple[EvidenceUse, ...] = (),
               rationale_holding_ids: tuple[str, ...] = (), missing_information: tuple[str, ...] = (),
               parents: tuple[CausalLink, ...] = ()) -> DecisionVersion:
        versions = self.versions(decision_id)
        question = self._questions[decision_id]
        if type(expected_version) is not int or expected_version != len(versions):
            raise ValueError("stale expected decision version")
        if option not in question.alternatives:
            raise ValueError("option is not an alternative")
        _confidence(confidence)
        require_text(reason, "reason")
        _strings(rationale_holding_ids, "rationale_holding_ids")
        _strings(missing_information, "missing_information")
        if type(evidence) is not tuple or any(type(e) is not EvidenceUse for e in evidence):
            raise TypeError("evidence must be a tuple of EvidenceUse")
        if len(set(evidence)) != len(evidence):
            raise ValueError("duplicate evidence use")
        if type(parents) is not tuple or any(type(p) is not CausalLink for p in parents):
            raise TypeError("parents must be a tuple of CausalLink")
        if len(set(parents)) != len(parents):
            raise ValueError("duplicate causal link")
        view = _present(self._store, self._history, actor_id)
        accessible = {e.holding.holding_id: e for e in view.entries}
        holding_ids = tuple(dict.fromkeys(rationale_holding_ids + tuple(e.holding_id for e in evidence)))
        if any(key not in accessible for key in holding_ids):
            raise ValueError("actor has no accessible holding for rationale/evidence")
        basis, grant_ref = "inferred_without_authority", None
        links = list(parents)
        if grant_id is not None:
            grant, authority_links = self._authority.evaluate(grant_id, actor_id, question.scope, option, tick=tick)
            basis, grant_ref = grant.basis, grant.ref
            links.extend(authority_links)
        else:
            links.extend(self._authority.context_links(actor_id, question.scope))
        if versions:
            links.append(CausalLink(versions[-1].event_id, "direct_cause"))
        for key in holding_ids:
            links.extend(self._lineage(accessible[key]))
        rationale_sources = {s for key in rationale_holding_ids for s in accessible[key].holding.source_ids}
        # A new justification version must not erase the interpretation's prior
        # dependencies. A question-level citation also cannot bypass an already
        # recorded choice's lineage; use exact old versions for new observations.
        interpretation_sources = rationale_sources | (set(versions[-1].source_ids) if versions else set())
        source_ids = set(interpretation_sources)
        findings = []
        for use in evidence:
            if use.subject == question.ref:
                target_sources = interpretation_sources
            elif use.subject.entity_type == "decision" and use.subject.entity_id == decision_id:
                target_sources = set(self.version(decision_id, use.subject.version).source_ids)
            else:
                raise ValueError("evidence must name this question or an existing decision version")
            if use.option not in question.alternatives:
                raise ValueError("evidence option is not an alternative")
            entry = accessible[use.holding_id]
            if entry.item.topic != question.topic:
                raise ValueError("evidence topic does not match the decision")
            sources = entry.holding.source_ids
            # Once admitted, the same assessment of the same informational
            # content remains support, even through a copied holding. Reuse is
            # not new evidence; metrics still count each source only once.
            admitted_before = any(
                finding.eligible and finding.item == entry.item.ref
                and finding.source_ids == sources
                and replace(finding.assessment, holding_id=use.holding_id) == use
                for prior in versions for finding in prior.evidence
            )
            exclusion = None
            if use.method == "verification":
                exclusion = "verification_only"
            elif not sources:
                exclusion = "unknown_sources"
            elif use.quality != "usable" or entry.holding.freshness != "current":
                exclusion = "weak_or_stale"
            elif set(sources) & target_sources and not admitted_before:
                exclusion = "shared_subject_source"
            findings.append(EvidenceFinding(use, entry.item.ref, entry.holding.ref, sources,
                                            exclusion is None, exclusion))
            source_ids.update(sources)
        # Include the choice itself in lineage so tests copied from an unsupported
        # interpretation still have a dependency even when there were no holdings.
        version_number = len(versions) + 1
        source_ids.add(f"decision:{decision_id}@{version_number}")
        backed = tuple(sorted({s for f in findings if f.eligible for s in f.source_ids}))
        support = self._support(option, tuple(findings))
        gaps = []
        if grant_ref is None:
            gaps.append("no_authority_claimed")
        if support != "supported":
            gaps.append("insufficient_independent_support")
        if missing_information:
            gaps.append("missing_information")
        fields = dict(decision_id=decision_id, version=version_number,
                      prior=versions[-1].ref if versions else None, actor_id=actor_id,
                      selected=option, confidence=confidence, authority_basis=basis, grant_ref=grant_ref,
                      support=support, evidence=tuple(findings), source_ids=tuple(sorted(source_ids)),
                      backed_source_ids=backed, rationale=tuple(accessible[k].holding.ref for k in rationale_holding_ids),
                      missing_information=missing_information, reason=reason)
        # Validate all caller data in the first append before changing any state.
        draft = DecisionVersion(**fields, event_id="pending")
        payload = _payload(draft)
        del payload["event_id"]
        payload.update(question=_payload(question), resolution="selected", justification_gaps=gaps)
        event = self._history.append(
            tick=tick, event_type="DecisionRevised" if versions else "DecisionSelected",
            command_id=command_id, correlation_id=correlation_id, payload=payload,
            entities=(question.ref, draft.ref), parents=tuple(dict.fromkeys(links)),
        )
        result = DecisionVersion(**fields, event_id=event.event_id)
        self._versions[decision_id] = versions + (result,)
        if gaps:
            self._history.append(
                tick=tick, event_type="AssumptionMade", command_id=command_id,
                correlation_id=correlation_id, entities=(result.ref,),
                parents=(CausalLink(event.event_id, "direct_cause"),),
                payload={"decision_id": decision_id, "version": version_number, "gaps": gaps,
                         "missing_information": list(missing_information)},
            )
        return result

    @staticmethod
    def _support(selected: str, findings: tuple[EvidenceFinding, ...]) -> str:
        if not findings:
            return "none"
        # Keep contradictions visible even if a precaution changes the choice or
        # some conflicting claims are weak. Report majority never resolves them.
        stances: dict[str, set[str]] = {}
        supporting_options = set()
        for finding in findings:
            use = finding.assessment
            if use.method != "verification":
                stances.setdefault(use.option, set()).add(use.stance)
                if use.stance == "supports":
                    supporting_options.add(use.option)
        if len(supporting_options) > 1 or any({"supports", "challenges"} <= s for s in stances.values()):
            return "conflicted"
        eligible = [f.assessment for f in findings if f.eligible]
        if any(e.option == selected and e.stance == "supports" for e in eligible):
            return "supported"
        if any((e.option == selected and e.stance == "challenges")
               or (e.option != selected and e.stance == "supports") for e in eligible):
            return "challenged"
        return "inconclusive" if eligible else "weak"
