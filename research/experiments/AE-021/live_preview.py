"""Bounded passive preview; authoritative setup/steps are Python-owned.

No shipping, private projection or management controls. Run from checkout root.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import uuid

from agent_empires.application.commands import PreviewSession
from agent_empires.application.scenarios import load_scenario
from agent_empires.application.services import DeliveryService
from agent_empires.adapters.transport.http import create_server
from agent_empires.simulation.actors import Actor
from agent_empires.simulation.communication import Channel


def prepare(run_id, seed=7):
    service = DeliveryService(load_scenario('scenarios/paymentco/scenario.json'),
                              run_id=run_id, root_seed=seed)
    for actor_id, profile, team, role in (
        ('agent.build', 'implementer', 'engineering', 'implementer'),
        ('agent.investigate', 'investigator', 'architecture', 'investigator'),
        ('agent.assure', 'assurance_ops', 'security', 'assurance ops')):
        service.register_actor(Actor(actor_id, 'agent', team), profile_id=profile,
                               role=role, command_id='preview.register.' + actor_id)
    comm = service.communication  # explicitly initialize the real authored edges
    for channel in (Channel('preview.context', 'sarah', 'agent.build', 2, 1),
                    Channel('preview.audit', 'priya', 'agent.assure', 3, 1),
                    Channel('preview.loss', 'ada', 'agent.investigate', 2, 1,
                            loss_probability=1.0)):
        comm.connect(channel, command_id='preview.connect.' + channel.channel_id,
                     correlation_id='preview.setup')
    for actor in ('agent.build', 'agent.investigate', 'jin'):
        service.start(actor, command_id='preview.work.' + actor)
    return PreviewSession(service)


def send_messages(session):
    service = session.service
    for channel, sender in (('preview.context', 'sarah'), ('preview.audit', 'priya'),
                            ('preview.loss', 'ada')):
        holding = service.knowledge.view_for(sender).entries[0].holding.holding_id
        service.communication.send(channel, holding, command_id='preview.send.' + channel,
                                   correlation_id='preview.messages')


def recording():
    session = prepare('ae021-fixture')
    initial = session.snapshot()
    stages = []
    cursor = initial['cursor']
    send_messages(session)
    for index in range(4):
        if index:
            ack = session.handle(dict(version=1, run_id=session.run_id,
                command_id=f'owner.step.{index}', operation='step', args={}))
            assert ack['status'] == 'accepted'
        snapshot = session.snapshot()
        stages.append(dict(batch=session.batch(cursor, 256), snapshot=snapshot))
        cursor = snapshot['cursor']
    assert len(stages[-1]['snapshot']['proposals']) == 3
    assert {t['status'] for t in stages[-1]['snapshot']['transfers']} == {'received', 'lost'}
    return dict(version=1, seed=7, initial_snapshot=initial, stages=stages,
                protocol='Real public snapshots/batches from DeliveryService and PreviewSession; no authored domain facts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-fixture', type=Path)
    parser.add_argument('--verify-fixture', type=Path)
    parser.add_argument('--run-id', default=None)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--duration', type=float, default=0, help='0 stays open until closed; finite diagnostics 8–300 seconds')
    parser.add_argument('--step-seconds', type=float, default=3, help='owner scheduling pace, 2–10 seconds')
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--capture', type=Path, help='PNG of Godot viewport only')
    parser.add_argument('--headless', action='store_true', help='socket integration diagnostic; does not prove a window')
    a = parser.parse_args()
    if a.record_fixture or a.verify_fixture:
        fixture = recording()
        if a.verify_fixture:
            assert json.loads(a.verify_fixture.read_text()) == fixture
            print('PASS: real Python fixture regenerates identically')
        else:
            with a.record_fixture.open('x') as f:
                json.dump(fixture, f, indent=2)
                f.write('\n')
        return
    if (a.duration != 0 and not max(8, 3 * a.step_seconds + 2) <= a.duration <= 300) or not 2 <= a.step_seconds <= 10:
        parser.error('duration or scheduling pace outside preview bounds')
    if a.capture and a.capture.exists():
        parser.error('refusing to overwrite capture evidence')
    session = prepare(a.run_id or 'preview-' + uuid.uuid4().hex, a.seed)
    server = None
    child = None
    selector = selectors.DefaultSelector()
    displayed = {}
    output_buffer = b''
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    try:
        server = create_server(session, port=a.port)
        server.timeout = 0.1
        endpoint = f'http://127.0.0.1:{server.server_address[1]}/command'
        argv = [a.godot, '--path', 'godot']
        if a.headless:
            argv += ['--headless']
        argv += ['--', '--endpoint=' + endpoint, '--run-id=' + session.run_id]
        if a.capture:
            argv += ['--capture=' + str(a.capture.resolve()), '--capture-after=11']
        child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        selector.register(child.stdout, selectors.EVENT_READ)
        print(json.dumps(dict(endpoint=endpoint, run_id=session.run_id,
                              godot_pid=child.pid, seed=a.seed)), flush=True)
        start = time.monotonic()
        sent, steps = False, 0
        while not stopped and child.poll() is None and (a.duration == 0 or time.monotonic() - start < a.duration):
            # One thread owns all domain/session calls; polling cannot step time.
            server.handle_request()
            for key, _ in selector.select(timeout=0):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output_buffer += chunk
                while b'\n' in output_buffer:
                    raw_line, output_buffer = output_buffer.split(b'\n', 1)
                    line = raw_line.decode('utf-8', errors='replace')
                    print(line, flush=True)
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(record, dict) and 'projection_snapshot' in record:
                        displayed[record['projection_snapshot']] = record
            elapsed = time.monotonic() - start
            if not sent and elapsed >= 1:
                send_messages(session)
                sent = True
            if steps < 3 and elapsed >= a.step_seconds * (steps + 1):
                steps += 1
                session.handle(dict(version=1, run_id=session.run_id,
                    command_id=f'owner.step.{steps}', operation='step', args={}))
        code = child.poll()
        if code not in (None, 0):
            raise RuntimeError(f'Godot child exited {code}')
        final_snapshot = session.snapshot()
        projection = displayed.get(final_snapshot['snapshot_id'])
        print(json.dumps(dict(final_snapshot=final_snapshot, owner_steps=steps,
                              godot_projection=projection)), flush=True)
        if a.duration == 0 and (stopped or code == 0):
            # User close/signal is normal; finite diagnostic runs still require
            # completed work and matching final projection below.
            print('Preview closed by user; no completion acceptance claimed', flush=True)
            return
        if steps != 3 or len(final_snapshot['proposals']) != 3:
            raise RuntimeError('Preview ended before three real work completions')
        if projection is None:
            raise RuntimeError('Godot did not report the final Python snapshot ID')
        assert projection['actor_ids'] == sorted(a['actor_id'] for a in final_snapshot['roster'])
        assert projection['proposal_ids'] == [p['proposal_id'] for p in final_snapshot['proposals']]
        assert projection['transfer_statuses'] == {t['transfer_id']: t['status'] for t in final_snapshot['transfers']}
        if a.capture and not a.capture.is_file():
            raise RuntimeError('Requested viewport PNG was not produced')
        print('PASS: live Godot projection matches final Python IDs and statuses', flush=True)
    finally:
        selector.close()
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        if child is not None and child.stdout is not None:
            child.stdout.close()
        if server is not None:
            server.server_close()
        print('Preview owner cleanup complete', flush=True)


if __name__ == '__main__':
    main()
