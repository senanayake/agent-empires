"""Finite clarification over explicit channels; answers are claims, never truth.

Single-consumer owner sharing the store, clock and history. Trusted setup supplies
channels and holder availability (absolute earliest service tick, None = absent).
The caller dispatches popped work; this owner never drains another owner's queue.
Request capacity rejects congestion; finite answer batches wait for channel slots.
No automatic delegation, empirical validation, dialogue or world lookup occurs.
"""
from dataclasses import asdict, dataclass, field

from .actors import require_text
from .clock import ScheduledCommand, SimulationClock, require_tick
from .communication import Channel
from .decisions import AuthorityRegistry, CapabilityProfile, DecisionQuestion, Decisions
from .events import CausalLink, EntityRef, Event, EventHistory, canonical_json
from .knowledge import ActorKnowledge, HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore
from .randomness import NamedRandomness

MODEL_VERSION = 'clarification-v1'


@dataclass(frozen=True, slots=True)
class Answer:
    holding_id: str
    proposition: str
    source_ids: tuple[str, ...]
    freshness: str
    authority_status: str
    grant_ref: EntityRef | None
    event_id: str


@dataclass(frozen=True, slots=True)
class ClarificationResult:
    command_id: str
    status: str
    completed_tick: int
    elapsed_ticks: int
    answers: tuple[Answer, ...]
    source_ids: tuple[str, ...]
    event_id: str


@dataclass(slots=True)
class _Query:
    question: DecisionQuestion
    requester: str
    holder: str
    request: Channel
    response: Channel
    start: int
    deadline: int
    available_at: int | None
    service_ticks: int
    grant_id: str | None
    asked: Event
    answers: list[Answer] = field(default_factory=list)
    remaining: int = 0
    truncated: bool = False


class Clarification:
    def __init__(self, store: KnowledgeStore, authority: AuthorityRegistry,
                 clock: SimulationClock, history: EventHistory, randomness: NamedRandomness):
        self._store, self._authority, self._clock = store, authority, clock
        self._history, self._rng = history, randomness
        self._channels: dict[str, tuple[Channel, Event]] = {}
        self._usage: dict[tuple[str, int], int] = {}
        self._queries: dict[str, _Query] = {}
        self._results: dict[str, ClarificationResult] = {}
        self._tasks: dict[str, tuple[ScheduledCommand, str, str, object]] = {}
        self._next_task = 0
        self.total_cost = 0

    def _present(self, actor_id: str) -> bool:
        self._store.view_for(actor_id)
        return not any(e.event_type == 'ActorDeparted' and e.payload['actor_id'] == actor_id
                       for e in self._history.events)

    def _synchronized(self):
        if self._history.events and self._history.events[-1].tick > self._clock.now:
            raise ValueError('clock must reach latest fact')

    def connect(self, channel: Channel) -> Event:
        self._synchronized()
        if type(channel) is not Channel:
            raise TypeError('expected Channel')
        if channel.channel_id in self._channels:
            raise ValueError('duplicate channel')
        if not self._present(channel.sender) or not self._present(channel.recipient):
            raise ValueError('channel endpoints must be present')
        event = self._history.append(
            tick=self._clock.now, event_type='ClarificationChannelConnected',
            command_id='clarification.connect.' + channel.channel_id, correlation_id='clarification.setup',
            payload={'channel': asdict(channel), 'cost': channel.connection_cost},
            entities=(EntityRef('channel', channel.channel_id, 1),))
        self._channels[channel.channel_id] = channel, event
        self.total_cost += channel.connection_cost
        return event

    def _schedule(self, tick: int, query: str, phase: str, data=None):
        key = f'clarification:{query}:{phase}:{self._next_task}'
        self._next_task += 1
        work = self._clock.schedule(tick, key, priority=1 if phase == 'timeout' else 0)
        self._tasks[key] = work, query, phase, data

    def ask(self, question: DecisionQuestion, *, requester: str, holder: str,
            request_channel: str, answer_channel: str, command_id: str, timeout: int,
            available_at: int | None = 0, service_ticks: int = 0, grant_id: str | None = None):
        """Admit a question, without acquiring any holder content or permission."""
        self._synchronized()
        if type(question) is not DecisionQuestion:
            raise TypeError('expected DecisionQuestion')
        require_text(command_id, 'command_id')
        require_tick(timeout)
        require_tick(service_ticks)
        if timeout == 0:
            raise ValueError('timeout must be positive')
        if available_at is not None:
            require_tick(available_at)
        if grant_id is not None:
            require_text(grant_id, 'grant_id')
        if command_id in self._queries:
            raise ValueError('duplicate clarification command')
        if not self._present(requester) or not self._present(holder):
            raise ValueError('clarification endpoints must be present')
        if request_channel not in self._channels or answer_channel not in self._channels:
            raise ValueError('unknown directed channel')
        request, request_event = self._channels[request_channel]
        response, response_event = self._channels[answer_channel]
        if ((request.sender, request.recipient) != (requester, holder)
                or (response.sender, response.recipient) != (holder, requester)):
            raise ValueError('channels do not form the requested round trip')
        usage = request_channel, self._clock.now
        if self._usage.get(usage, 0) >= request.capacity:
            raise ValueError('request channel capacity exhausted')
        event = self._history.append(
            tick=self._clock.now, event_type='ClarificationRequested', command_id=command_id,
            correlation_id=command_id, entities=(question.ref,),
            parents=(CausalLink(request_event.event_id, 'direct_cause'),
                     CausalLink(response_event.event_id, 'association')),
            payload={'requester': requester, 'holder': holder, 'question': question.decision_id,
                     'deadline': self._clock.now + timeout, 'available_at': available_at,
                     'service_ticks': service_ticks, 'cost': request.transfer_cost,
                     'request_channel': request_channel, 'answer_channel': answer_channel,
                     'claimed_grant_id': grant_id})
        q = _Query(question, requester, holder, request, response, self._clock.now,
                   self._clock.now + timeout, available_at, service_ticks, grant_id, event)
        self._queries[command_id] = q
        self._usage[usage] = self._usage.get(usage, 0) + 1
        self.total_cost += request.transfer_cost
        self._schedule(min(q.deadline, q.start + request.latency), command_id, 'request')
        return event

    def _draw(self, command: str, purpose: str):
        return self._rng.stream(canonical_json([MODEL_VERSION, command, purpose]).decode('ascii')).random()

    def _fact(self, command: str, kind: str, payload: dict, parents=(), entities=()):
        q = self._queries[command]
        return self._history.append(
            tick=self._clock.now, event_type=kind, command_id=command, correlation_id=command,
            parents=(CausalLink(q.asked.event_id, 'direct_cause'),) + parents,
            entities=entities, payload=payload)

    def _finish(self, command: str, status: str):
        q = self._queries[command]
        sources = tuple(sorted({s for a in q.answers for s in a.source_ids}))
        event = self._fact(command, 'ClarificationCompleted',
                           {'status': status, 'elapsed_ticks': self._clock.now - q.start,
                            'source_ids': list(sources), 'answer_count': len(q.answers)},
                           tuple(CausalLink(a.event_id, 'supporting_evidence') for a in q.answers))
        self._results[command] = ClarificationResult(command, status, self._clock.now,
                                                     self._clock.now - q.start, tuple(q.answers), sources, event.event_id)

    def dispatch(self, work: ScheduledCommand):
        """Resolve exactly one popped task at its scheduled tick."""
        self._synchronized()
        task = self._tasks.get(work.command_id)
        if task is None or task[0] != work or work.tick != self._clock.now:
            raise ValueError('unknown, completed or not-due clarification task')
        _, command, phase, data = self._tasks.pop(work.command_id)
        q = self._queries[command]
        if phase == 'timeout':
            self._finish(command, 'timed_out')
        elif phase == 'request':
            if q.start + q.request.latency > q.deadline:
                self._finish(command, 'timed_out')
            elif (q.available_at is None or not self._present(q.holder)
                  or self._draw(command, 'request-loss') < q.request.loss_probability):
                self._schedule(q.deadline, command, 'timeout')
            else:
                ready = max(self._clock.now, q.available_at) + q.service_ticks
                self._schedule(min(ready, q.deadline), command,
                               'response' if ready <= q.deadline else 'timeout')
        elif phase == 'response':
            entries = tuple(e for e in self._store.view_for(q.holder).entries
                            if e.item.topic == q.question.topic
                            and e.item.proposition in q.question.alternatives)
            if not self._present(q.holder) or not entries:
                self._finish(command, 'no_answer')
                return
            for index, entry in enumerate(entries):
                sent = self._clock.now
                while self._usage.get((q.response.channel_id, sent), 0) >= q.response.capacity:
                    sent += 1
                if sent + q.response.latency > q.deadline:
                    q.truncated = True
                    continue
                slot = q.response.channel_id, sent
                self._usage[slot] = self._usage.get(slot, 0) + 1
                self._schedule(sent, command, 'send', (index, entry))
                q.remaining += 1
            if q.truncated:
                self._schedule(q.deadline, command, 'timeout')
            elif not q.remaining:
                self._finish(command, 'no_answer')
        elif phase == 'send':
            index, entry = data
            self.total_cost += q.response.transfer_cost
            acquisition = next(e for e in reversed(self._history.events)
                               if e.event_type in ('KnowledgeHoldingRecorded', 'KnowledgeTransferred')
                               and any(r.entity_type == 'knowledge_holding'
                                       and r.entity_id == entry.holding.holding_id for r in e.entities))
            access = next(e for e in reversed(self._history.events)
                          if e.event_type in ('KnowledgeHoldingRecorded', 'HoldingAccessChanged')
                          and entry.holding.ref in e.entities)
            sent = self._fact(command, 'ClarificationAnswerSent',
                              {'holder': q.holder, 'source_holding': entry.holding.ref.as_dict(),
                               'source_ids': list(entry.holding.source_ids), 'cost': q.response.transfer_cost,
                               'delivery_tick': self._clock.now + q.response.latency},
                              tuple(dict.fromkeys(CausalLink(e.event_id, 'supporting_evidence')
                                                  for e in (acquisition, access))))
            self._schedule(self._clock.now + q.response.latency, command, 'receive', (index, entry, sent))
        elif phase == 'receive':
            index, entry, sent = data
            loss = self._draw(command, f'answer-{index}-loss')
            distortion = self._draw(command, f'answer-{index}-distortion')
            if not self._present(q.requester) or loss < q.response.loss_probability:
                self._fact(command, 'ClarificationAnswerLost', {'source_ids': list(entry.holding.source_ids),
                           'loss_draw': loss}, (CausalLink(sent.event_id, 'direct_cause'),))
            else:
                item = entry.item
                rule = q.response.distortion
                distorted = (rule is not None and item.topic == rule.topic and item.proposition == rule.original
                             and distortion < q.response.distortion_probability)
                if distorted:
                    item = KnowledgeItem(f'clarification:{sent.event_id}:distorted', 1, item.topic, rule.alternative)
                    self._store.register_item(item)
                holding = KnowledgeHolding(f'clarification:{sent.event_id}:holding', item.ref,
                                           HolderRef('actor', q.requester), entry.holding.source_ids,
                                           entry.holding.confidence, entry.holding.freshness, entry.holding.explicit)
                recorded = self._store.record_holding(holding, tick=self._clock.now, command_id=command,
                           correlation_id=command, parents=(CausalLink(sent.event_id, 'direct_cause'),))
                grant_ref, status, links = None, 'not_claimed', ()
                if q.grant_id is not None:
                    try:
                        grant, links = self._authority.evaluate(q.grant_id, q.holder, q.question.scope,
                                                                item.proposition, tick=self._clock.now)
                        grant_ref, status = grant.ref, 'valid'
                    except ValueError:
                        status = 'invalid'
                event = self._fact(command, 'KnowledgeTransferred',
                                   {'received_holding': holding.ref.as_dict(), 'source_ids': list(holding.source_ids),
                                    'holder': q.holder, 'authority_status': status,
                                    'claimed_grant_id': q.grant_id,
                                    'grant_ref': grant_ref.as_dict() if grant_ref else None,
                                    'freshness': holding.freshness, 'distorted': distorted,
                                    'original_item': entry.item.ref.as_dict(), 'received_item': item.ref.as_dict(),
                                    'loss_draw': loss, 'distortion_draw': distortion},
                                   (CausalLink(sent.event_id, 'direct_cause'),
                                    CausalLink(recorded.event_id, 'direct_cause')) + links,
                                   (item.ref, holding.ref))
                q.answers.append(Answer(holding.holding_id, item.proposition, holding.source_ids,
                                        holding.freshness, status, grant_ref, event.event_id))
            q.remaining -= 1
            if q.remaining == 0 and not q.truncated:
                propositions = {a.proposition for a in q.answers}
                status = 'conflicted' if len(propositions) > 1 else 'answered' if q.answers else 'no_answer'
                self._finish(command, status)

    def result(self, command_id: str) -> ClarificationResult:
        if command_id not in self._results:
            raise ValueError('clarification has not completed')
        return self._results[command_id]

    def propose(self, command_id: str, profile: CapabilityProfile):
        """Use fresh accessible current claims; stale claims remain in the audit."""
        self.result(command_id)
        q = self._queries[command_id]
        view = self._store.view_for(q.requester)
        current = ActorKnowledge(view.actor_id, tuple(e for e in view.entries if e.holding.freshness == 'current'))
        return profile.propose(q.question, current)

    def select(self, query_id: str, decisions: Decisions, profile: CapabilityProfile, *,
               expected_version: int, command_id: str):
        """Append an actor choice. A holder's grant is never a requester grant."""
        result = self.result(query_id)
        q = self._queries[query_id]
        option, holdings = self.propose(query_id, profile)
        return decisions.select(q.question.decision_id, option, actor_id=q.requester,
                                expected_version=expected_version, tick=self._clock.now,
                                command_id=command_id, correlation_id=query_id,
                                confidence=profile.confidence, rationale_holding_ids=holdings,
                                reason='clarification claims and capability preference',
                                missing_information=('independent validation pending',),
                                parents=(CausalLink(result.event_id, 'supporting_evidence'),))
