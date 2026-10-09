"""Versioned passive-preview commands and public projections, without wire I/O."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json

from .services import DeliveryService
from agent_empires.simulation.events import canonical_json

VERSION = 1
MAX_BATCH = 256
MAX_COMMANDS = 4096


class ProtocolError(ValueError):
    """The consumer must discard the batch and request a fresh snapshot."""


def _text(value):
    return type(value) is str and bool(value.strip()) and len(value) <= 128


def rejection(command_id, run_id, error):
    return dict(version=VERSION, run_id=run_id, command_id=command_id,
                ack_id=f'{run_id}:ack:{command_id}' if command_id else None,
                status='rejected', error=error)


class PreviewSession:
    """Single-consumer command owner; no ambient time or management commands.

    A trusted caller prepares the real service/workload before exposing it.
    Replay caching is bounded and lasts only for this process/run.
    """
    def __init__(self, service: DeliveryService):
        self.service = service
        self.run_id = service.history.run_id
        if not _text(self.run_id):
            raise ValueError('run_id must be a nonempty string of at most 128 characters')
        self.paused = True
        self._acks = {}

    def handle(self, request):
        cid = request.get('command_id') if type(request) is dict else None
        cid = cid if _text(cid) else None
        def reject(code):
            return rejection(cid, self.run_id, code)
        if type(request) is not dict:
            return reject('malformed_command')
        if type(request.get('version')) is not int or request['version'] != VERSION:
            return reject('incompatible_version')
        if set(request) != {'version', 'run_id', 'command_id', 'operation', 'args'} or cid is None:
            return reject('malformed_command')
        if request['run_id'] != self.run_id:
            return reject('wrong_run')
        if not _text(request['operation']) or type(request['args']) is not dict:
            return reject('malformed_command')
        try:
            encoded = canonical_json(request)
        except (TypeError, ValueError):
            return reject('malformed_command')
        if cid in self._acks:
            old_request, ack = self._acks[cid]
            return deepcopy(ack) if encoded == old_request else reject('duplicate_id')
        if len(self._acks) >= MAX_COMMANDS:
            return reject('session_capacity')
        op, args = request['operation'], request['args']
        error, result = None, None
        if op == 'pause':
            if set(args) != {'paused'} or type(args['paused']) is not bool:
                error = 'malformed_command'
            else:
                self.paused = args['paused']
                result = {'paused': self.paused}
        elif op in ('step', 'advance', 'snapshot'):
            if args:
                error = 'malformed_command'
            elif op == 'snapshot':
                result = self.snapshot()
            elif (op == 'step') != self.paused:
                error = 'not_paused' if op == 'step' else 'paused'
            else:
                before = len(self.service.history.events)
                self.service.step()
                result = {'changed': before != len(self.service.history.events)}
        elif op == 'events':
            if (set(args) != {'cursor', 'limit'} or type(args['cursor']) is not int
                    or args['cursor'] < 0 or type(args['limit']) is not int
                    or not 1 <= args['limit'] <= MAX_BATCH):
                error = 'malformed_command'
            elif args['cursor'] > len(self.service.history.events):
                error = 'invalid_cursor'
            else:
                result = self.batch(args['cursor'], args['limit'])
        else:
            error = 'unknown_operation'
        ack = reject(error) if error else dict(
            version=VERSION, run_id=self.run_id, command_id=cid,
            ack_id=f'{self.run_id}:ack:{cid}', status='accepted',
            tick=self.service.clock.now, cursor=len(self.service.history.events), result=result)
        self._acks[cid] = encoded, deepcopy(ack)
        return ack

    def snapshot(self):
        s = self.service
        channels, transfers = self._public_graph()
        state = dict(channels=channels, transfers=transfers, version=VERSION, run_id=self.run_id, scenario_hash=s.scenario.sha256,
            model_version='delivery-preview-v1', tick=s.clock.now,
            cursor=len(s.history.events), paused=self.paused,
            goal=asdict(s.goal), work_item=asdict(s.work_item),
            roster=[dict(actor_id=a.actor_id, kind=a.kind, team_id=a.team_id,
                         role=s.organization.role_for(a.actor_id))
                    for a in s.knowledge.actors if s.knowledge.is_present(a.actor_id)],
            decisions=[dict(decision_id=d, alternatives=list(s.scenario.question_for(d).alternatives))
                       for d in s.work_item.required_decisions],
            proposals=[dict(proposal_id=p.proposal_id, actor_id=p.actor_id,
                            completion_tick=p.completed_tick,
                            assessments=self._assessments_for(p.event_id)) for p in s.proposals])
        # asdict includes tuple refs; JSON conversion makes detached wire-safe data.
        state = json.loads(json.dumps(state, allow_nan=False))
        digest = hashlib.sha256(canonical_json(state)).hexdigest()
        return dict(state, snapshot_id=f'{self.run_id}:snapshot:{digest}')

    def _public_graph(self):
        # Rehydrate recorded facts, without lazily initializing communication.
        channels, transfers = {}, {}
        for event in self.service.history.events:
            fact = self._project(event)
            payload, kind = fact['payload'], fact['event_type']
            if kind == 'ChannelConnected':
                channel = payload['channel']
                channels[channel['channel_id']] = channel
            elif kind == 'ChannelRetired':
                channels.pop(payload['channel_id'], None)
            elif kind == 'TransferSent':
                transfers[event.event_id] = dict(payload, sent_tick=event.tick, status='pending')
            elif kind in ('KnowledgeTransferred', 'InformationLost'):
                transfer = transfers.get(payload['transfer_id'])
                if transfer is not None:
                    transfer.update(status='received' if kind == 'KnowledgeTransferred' else 'lost',
                                    resolved_tick=event.tick)
        return list(channels.values()), list(transfers.values())

    def _assessments_for(self, proposal_event_id):
        for event in self.service.history.events:
            if (event.event_type == 'VerificationCompleted'
                    and any(p.event_id == proposal_event_id for p in event.parents)):
                return self._project(event)['payload']['assessments']
        return []

    def batch(self, cursor, limit):
        history = self.service.history.events
        events = [self._project(e) for e in history[cursor:cursor + limit]]
        end = cursor + len(events)
        return dict(version=VERSION, run_id=self.run_id,
                    batch_id=f'{self.run_id}:batch:{cursor}:{end}', cursor=cursor,
                    next_cursor=end, head_cursor=len(history), events=events)

    @staticmethod
    def _project(event):
        # Deny by default: private knowledge, functions, channel draws and world
        # audit remain in Python. Redacted placeholders keep contiguous cursors.
        fields = {
            'GoalDeclared': ('goal_id', 'intent', 'measure', 'target', 'observation_window'),
            'WorkItemCreated': ('work_item_id', 'text'),
            'DecisionRequired': ('decision_id',),
            'WorkStarted': ('actor_id', 'completion_tick', 'resource_cost'),
            'ChangeProposalCreated': ('resource_cost',),
            'VerificationCompleted': ('assessments', 'checks'),
            'ActorDeparted': ('actor_id',),
            'ActorReplaced': ('departing_actor', 'replacement_actor', 'assigned_role'),
            'ActorRegistered': ('actor_id', 'kind', 'team_id'),
            'WorkCancelled': ('actor_id', 'reason', 'retained_resource_cost'),
            'ChannelConnected': ('channel',),
            'ChannelRetired': ('channel_id', 'actor_id'),
            'TransferSent': ('channel_id', 'sender', 'recipient', 'units', 'delivery_tick'),
            'KnowledgeTransferred': ('channel_id', 'sender', 'recipient'),
            'InformationLost': ('channel_id', 'sender', 'recipient', 'reason'),
        }
        allowed = fields.get(event.event_type)
        payload = event.payload
        projected = {k: payload[k] for k in allowed if k in payload} if allowed else {}
        if event.event_type == 'ChannelConnected':
            projected = {'channel': {k: payload['channel'][k]
                                    for k in ('channel_id', 'sender', 'recipient', 'latency')}}
        elif event.event_type in ('TransferSent', 'KnowledgeTransferred', 'InformationLost'):
            projected['transfer_id'] = (event.event_id if event.event_type == 'TransferSent'
                                        else event.parents[0].event_id)
        if event.event_type == 'VerificationCompleted':
            projected = {'assessments': [
                {k: a[k] for k in ('dimension', 'status', 'method')}
                for a in payload['assessments']]}
        return dict(event_id=event.event_id, sequence=event.sequence, tick=event.tick,
                    schema_version=event.schema_version,
                    event_type=event.event_type if allowed is not None else 'Redacted',
                    command_id=event.command_id if allowed is not None else None,
                    correlation_id=event.correlation_id if allowed is not None else None,
                    payload=projected)


class EventCursor:
    """Atomic batch admission; a gap/old run/version/order requires resnapshot."""
    def __init__(self, snapshot):
        if (type(snapshot) is not dict or snapshot.get('version') != VERSION
                or type(snapshot.get('version')) is not int or not _text(snapshot.get('run_id'))
                or type(snapshot.get('cursor')) is not int or snapshot['cursor'] < 0):
            raise ProtocolError('invalid snapshot')
        self.run_id, self.cursor = snapshot['run_id'], snapshot['cursor']

    def accept(self, batch):
        if (type(batch) is not dict or type(batch.get('version')) is not int
                or batch['version'] != VERSION or batch.get('run_id') != self.run_id
                or type(batch.get('cursor')) is not int or batch['cursor'] != self.cursor
                or type(batch.get('events')) is not list
                or type(batch.get('next_cursor')) is not int
                or batch['next_cursor'] != self.cursor + len(batch['events'])
                or type(batch.get('head_cursor')) is not int
                or batch['head_cursor'] < batch['next_cursor']
                or batch.get('batch_id') != f"{self.run_id}:batch:{self.cursor}:{batch['next_cursor']}"):
            raise ProtocolError('incompatible or discontinuous batch; request snapshot')
        for sequence, event in enumerate(batch['events'], start=self.cursor):
            if (type(event) is not dict or type(event.get('sequence')) is not int
                    or event['sequence'] != sequence
                    or event.get('event_id') != f'{self.run_id}:event:{sequence}'
                    or type(event.get('schema_version')) is not int or event['schema_version'] != 1):
                raise ProtocolError('gap, duplicate or out-of-order event; request snapshot')
        self.cursor = batch['next_cursor']
        return deepcopy(batch['events'])
