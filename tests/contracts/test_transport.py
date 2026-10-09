"""Behavioral contracts shared by the passive preview and its replaceable wire."""
import ast
from copy import deepcopy
import http.client
import json
import io
from pathlib import Path
import threading

import pytest

from agent_empires.application.commands import PreviewSession, EventCursor, ProtocolError
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.adapters.transport.http import create_server, create_handler


@pytest.fixture
def session():
    service = DeliveryService(load_scenario('scenarios/paymentco/scenario.json'),
                              run_id='contract', root_seed=7)
    service.start('jin', command_id='preview.work')
    return PreviewSession(service)


def command(operation='snapshot', command_id='c1', args=None, **changes):
    return dict(version=1, run_id='contract', command_id=command_id,
                operation=operation, args={} if args is None else args, **changes)


@pytest.fixture
def live_wire(session):
    server = create_server(session, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def send(value):
        conn = http.client.HTTPConnection(*server.server_address, timeout=3)
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        conn.request('POST', '/command', body, {'Content-Type': 'application/json'})
        response = conn.getresponse()
        result = response.status, json.loads(response.read())
        conn.close()
        return result
    yield send
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


@pytest.fixture
def wire(session):
    # Exercise real HTTP parsing/serialization without requiring kernel sockets.
    def send(value):
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        request = (b'POST /command HTTP/1.0\r\nContent-Type: application/json\r\n'
                   + f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
        return exchange(session, request)
    return send


def exchange(session, request):
    class StreamSocket:
        def __init__(self): self.output = bytearray()
        def makefile(self, *args): return io.BytesIO(request)
        def settimeout(self, timeout): pass
        def sendall(self, data): self.output.extend(data)
    sock = StreamSocket()
    create_handler(session)(sock, ('127.0.0.1', 1), None)
    header, body = bytes(sock.output).split(b'\r\n\r\n', 1)
    return int(header.split(b' ')[1]), json.loads(body)


def test_loopback_round_trip(live_wire):
    assert live_wire(command())[1]['status'] == 'accepted'
    assert live_wire(command('step', 'step'))[1]['status'] == 'accepted'
    snapshot = live_wire(command(command_id='reconnect'))[1]['result']
    assert snapshot['proposals'][0]['actor_id'] == 'jin'


def test_serialized_round_trip_and_reconnect(wire):
    status, first = wire(command())
    assert status == 200 and first['status'] == 'accepted'
    snapshot = first['result']
    assert snapshot['snapshot_id'].startswith('contract:snapshot:')
    assert len(snapshot['roster']) == 10
    status, stepped = wire(command('step', 'step'))
    assert stepped['status'] == 'accepted' and stepped['tick'] > 0
    # Each wire call opens a fresh connection. Reconnect obtains authoritative state.
    _, latest = wire(command(command_id='reconnect'))
    assert latest['result']['cursor'] > snapshot['cursor']
    assert latest['result']['proposals'][0]['actor_id'] == 'jin'
    assert latest['result']['paused'] is True


@pytest.mark.parametrize('body,code', [
    (b'{', 'malformed_command'),
    (b'{"version":1,"version":2}', 'malformed_command'),
    (b'[]', 'malformed_command'),
    (b'{"version":NaN}', 'malformed_command'),
    (command() | {'version': 2}, 'incompatible_version'),
    (command() | {'version': True}, 'incompatible_version'),
    (command() | {'extra': 1}, 'malformed_command'),
    (command() | {'run_id': 'old'}, 'wrong_run'),
    (command() | {'command_id': ''}, 'malformed_command'),
    (command() | {'operation': 'replace_actor'}, 'unknown_operation'),
    (command('step', args={'ticks': 1}), 'malformed_command'),
    (command('events', args={'cursor': True, 'limit': 1}), 'malformed_command'),
    (command('events', args={'cursor': -1, 'limit': 1}), 'malformed_command'),
    (command('events', args={'cursor': 999999, 'limit': 1}), 'invalid_cursor'),
    (command('events', args={'cursor': 0, 'limit': 257}), 'malformed_command'),
])
def test_rejection_does_not_mutate(session, wire, body, code):
    before = session.service.history.canonical_bytes(), session.service.clock.now
    status, response = wire(body)
    assert status == 400 and response['status'] == 'rejected'
    assert response['error'] == code
    assert before == (session.service.history.canonical_bytes(), session.service.clock.now)


def test_duplicate_is_exact_original_ack_and_never_steps_twice(session):
    request = command('step')
    ack = session.handle(request)
    history = session.service.history.canonical_bytes()
    assert session.handle(request) == ack
    assert session.service.history.canonical_bytes() == history
    assert session.handle(command('pause', args={'paused': False}))['error'] == 'duplicate_id'
    # Returned mutable data cannot corrupt the remembered acknowledgment.
    ack['status'] = 'corrupted'
    assert session.handle(request)['status'] == 'accepted'


def test_pause_and_empty_step(session):
    tick = session.service.clock.now
    assert session.handle(command('pause', args={'paused': False}))['status'] == 'accepted'
    assert session.service.clock.now == tick
    assert session.handle(command('step', 'blocked'))['error'] == 'not_paused'
    assert session.handle(command('advance', 'advance'))['status'] == 'accepted'
    assert session.handle(command('pause', 'pause', {'paused': True}))['status'] == 'accepted'
    before = session.service.history.canonical_bytes()
    result = session.handle(command('step', 'empty'))
    assert result['status'] == 'accepted' and result['result']['changed'] is False
    assert before == session.service.history.canonical_bytes()


def test_event_gap_order_duplicate_and_run_are_rejected(session):
    snapshot = session.handle(command())['result']
    consumer = EventCursor(snapshot)
    session.handle(command('step', 'step'))
    batch = session.handle(command('events', 'events', {'cursor': snapshot['cursor'], 'limit': 256}))['result']
    assert len(batch['events']) >= 2
    for mutation in ('gap', 'order', 'duplicate', 'run', 'version', 'id'):
        bad = deepcopy(batch)
        if mutation == 'gap': bad['events'].pop(0)
        if mutation == 'order': bad['events'].reverse()
        if mutation == 'duplicate': bad['events'].append(bad['events'][-1])
        if mutation == 'run': bad['run_id'] = 'old'
        if mutation == 'version': bad['version'] = 2
        if mutation == 'id': bad['events'][0]['event_id'] = 'wrong'
        with pytest.raises(ProtocolError): consumer.accept(bad)
        assert consumer.cursor == snapshot['cursor']
    consumer.accept(batch)
    assert consumer.cursor == batch['next_cursor']
    with pytest.raises(ProtocolError): consumer.accept(batch)


def test_pagination_and_redaction(session):
    cursor, all_events = 0, []
    while cursor < len(session.service.history.events):
        batch = session.handle(command('events', str(cursor), {'cursor': cursor, 'limit': 3}))['result']
        assert batch['cursor'] == cursor
        all_events.extend(batch['events'])
        cursor = batch['next_cursor']
    assert [e['sequence'] for e in all_events] == list(range(cursor))
    serialized = json.dumps(all_events) + json.dumps(session.handle(command())['result'])
    for private in ('historical_scope', 'world_variants', 'source_ids', 'function_holders', 'loss_draw'):
        assert private not in serialized
    assert any(e['event_type'] == 'Redacted' for e in all_events)


def test_snapshot_is_live_after_trusted_replacement(session):
    from agent_empires.simulation.actors import Actor
    session.service.replace_actor('sarah', Actor('new', 'agent', 'engineering'),
        profile_id='implementer', role='developer', command_id='trusted.replace')
    snapshot = session.handle(command())['result']
    assert 'sarah' not in [a['actor_id'] for a in snapshot['roster']]
    assert 'new' in [a['actor_id'] for a in snapshot['roster']]
    assert 'domain_interpreter' not in json.dumps(snapshot)


def test_domain_import_boundary():
    allowed = {'__future__', 'dataclasses', 'json', 'types', 'typing', 'heapq',
               'hashlib', 'random', 'math', 'collections', 'decimal', 'enum', 'fractions'}
    for path in Path('src/agent_empires/simulation').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(n.name.split('.')[0] in allowed for n in node.names), path
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1, path
                else:
                    assert node.module.split('.')[0] in allowed, path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != '__import__', path
    # The selected adapter reaches only application, never simulation directly.
    for path in Path('src/agent_empires/adapters/transport').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                assert 'simulation' not in (node.module or ''), path


@pytest.mark.parametrize('headers,body', [
    (b'Content-Length: -1\r\n', b''),
    (b'Content-Length: 65537\r\n', b''),
    (b'Content-Length: 1\r\nContent-Length: 1\r\n', b'{'),
    (b'Transfer-Encoding: chunked\r\nContent-Length: 1\r\n', b'{'),
    (b'Content-Length: 2\r\n', b'{'),
    (b'Content-Length: 1\r\n', b'\xff'),
])
def test_malformed_http_framing(session, headers, body):
    before = session.service.history.canonical_bytes()
    status, ack = exchange(session, b'POST /command HTTP/1.0\r\n'
        b'Content-Type: application/json\r\n' + headers + b'\r\n' + body)
    assert status == 400 and ack['error'] == 'malformed_command'
    assert before == session.service.history.canonical_bytes()


def test_disconnect_after_commit_is_recoverable_by_same_id(session, wire):
    body = json.dumps(command('step', 'lost')).encode()
    class Disconnected:
        def makefile(self, *args):
            return io.BytesIO(b'POST /command HTTP/1.0\r\nContent-Type: application/json\r\n'
                + f'Content-Length: {len(body)}\r\n\r\n'.encode() + body)
        def settimeout(self, timeout): pass
        def sendall(self, data): raise BrokenPipeError('client left before acknowledgment')
    create_handler(session)(Disconnected(), ('127.0.0.1', 1), None)
    history = session.service.history.canonical_bytes()
    assert session.service.proposals
    assert wire(command('step', 'lost'))[1]['status'] == 'accepted'
    assert history == session.service.history.canonical_bytes()


def test_redaction_survives_new_private_fact(session, wire):
    service = session.service
    service.history.append(tick=service.clock.now, event_type='FuturePrivateFact',
        command_id='secret-command', correlation_id='secret-correlation',
        payload={'secret': 'private world answer'})
    _, ack = wire(command('events', args={'cursor': 0, 'limit': 256}))
    final = ack['result']['events'][-1]
    assert final['event_type'] == 'Redacted' and final['payload'] == {}
    assert final['command_id'] is None and final['correlation_id'] is None
    assert 'secret' not in json.dumps(ack)


def test_capacity_rejection_preserves_existing_idempotency(session, monkeypatch):
    import agent_empires.application.commands as commands
    monkeypatch.setattr(commands, 'MAX_COMMANDS', 1)
    first = session.handle(command('step'))
    history = session.service.history.canonical_bytes()
    assert session.handle(command(command_id='new'))['error'] == 'session_capacity'
    assert session.handle(command('step')) == first
    assert session.service.history.canonical_bytes() == history


def test_polling_and_pause_do_not_change_seeded_domain_history(session):
    original = session.service.history.canonical_bytes()
    session.handle(command())
    session.handle(command('events', 'poll', {'cursor': 0, 'limit': 256}))
    session.handle(command('pause', 'resume', {'paused': False}))
    session.handle(command('pause', 'pause', {'paused': True}))
    assert original == session.service.history.canonical_bytes()
    # A matched fresh run receives only the same explicit domain step.
    control = DeliveryService(load_scenario('scenarios/paymentco/scenario.json'),
                              run_id='contract', root_seed=7)
    control.start('jin', command_id='preview.work')
    control.step()
    session.handle(command('step', 'step'))
    assert session.service.history.canonical_bytes() == control.history.canonical_bytes()


def test_reconnect_retains_verification_unknown_dimensions(session, wire):
    wire(command('step', 'step'))
    _, ack = wire(command(command_id='reconnect'))
    assessments = ack['result']['proposals'][0]['assessments']
    statuses = {a['dimension']: a['status'] for a in assessments}
    assert statuses['verification_status'] == 'pass'
    assert statuses['validation_status'] == 'unknown'
    assert statuses['outcome_fitness'] == 'unknown'
    _, batch = wire(command('events', 'events', {'cursor': 0, 'limit': 256}))
    event = next(e for e in batch['result']['events'] if e['event_type'] == 'VerificationCompleted')
    assert event['payload']['assessments'] == assessments
    assert 'source_dependencies' not in json.dumps(event)


def test_public_graph_queries_do_not_initialize_or_mutate_domain(session):
    service = session.service
    before = service.history.canonical_bytes(), service.clock.now
    assert session.snapshot()['channels'] == []
    assert session.snapshot()['transfers'] == []
    assert before == (service.history.canonical_bytes(), service.clock.now)
    channels = service.communication.channels
    before = service.history.canonical_bytes()
    snapshot = session.snapshot()
    assert {c['channel_id'] for c in snapshot['channels']} == {c.channel_id for c in channels}
    assert set(snapshot['channels'][0]) == {'channel_id', 'sender', 'recipient', 'latency'}
    snapshot['channels'][0]['sender'] = 'corrupted'
    assert session.snapshot()['channels'][0]['sender'] != 'corrupted'
    assert service.history.canonical_bytes() == before


def test_public_transfer_reconnect_preserves_actual_status_and_redaction(session):
    s = session.service
    comm = s.communication
    entry = s.knowledge.view_for('sarah').entries[0]
    comm.send('sarah.to.jin', entry.holding.holding_id,
              command_id='public.message', correlation_id='public.message')
    sent = next(e for e in s.history.events if e.event_type == 'TransferSent')
    initial = session.snapshot()['transfers']
    assert len(initial) == 1 and initial[0]['status'] == 'pending'
    assert initial[0]['transfer_id'] == sent.event_id
    s.step()
    latest = session.snapshot()['transfers'][0]
    assert latest['transfer_id'] == sent.event_id and latest['status'] == 'received'
    batch = session.batch(0, 256)
    transfers = [e for e in batch['events'] if e['event_type'] in ('TransferSent', 'KnowledgeTransferred')]
    assert len(transfers) == 2
    assert all(e['payload']['transfer_id'] == sent.event_id for e in transfers)
    text = json.dumps(batch)+json.dumps(session.snapshot())
    for key in ('source_holding','source_ids','received_holding','loss_draw', 'distortion_draw','proposition','function_holders'):
        assert key not in text
    assert entry.item.proposition not in text


def test_public_graph_removes_retired_edges_without_losing_sent_history(session):
    from agent_empires.simulation.actors import Actor
    s = session.service
    s.communication
    s.replace_actor('sarah', Actor('agent-a','agent','engineering'),
                    profile_id='implementer',role='developer',command_id='replace.public')
    assert all('sarah' not in (c['sender'],c['recipient']) for c in session.snapshot()['channels'])
    events = session.batch(0,256)['events']
    assert any(e['event_type']=='ChannelRetired' for e in events)
