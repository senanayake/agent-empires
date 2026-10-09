"""Real fixture/public-boundary checks without kernel socket permissions."""
import importlib.util
import io
import json
from pathlib import Path
import io
import sys

import pytest

spec = importlib.util.spec_from_file_location('ae021_preview', Path(__file__).with_name('live_preview.py'))
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def test_recording_is_real_repeatable_public_state():
    fixture = preview.recording()
    assert fixture == preview.recording()
    assert fixture == json.loads(Path('godot/tests/fixtures/paymentco.json').read_text())
    first, last = fixture['initial_snapshot'], fixture['stages'][-1]['snapshot']
    assert len(first['roster']) == 13
    assert len({a['team_id'] for a in first['roster']}) == 5
    assert len(last['proposals']) == 3
    assert last['tick'] > first['tick']
    text = json.dumps(fixture)
    for forbidden in ('proposition', 'function_holders', 'world_variants', 'source_ids', 'loss_draw', 'distortion_draw'):
        assert forbidden not in text
    assert {t['status'] for t in last['transfers']} == {'received', 'lost'}


def test_polling_does_not_execute_work_or_deliver_pending_messages():
    session = preview.prepare('passive')
    preview.send_messages(session)
    before = session.service.history.canonical_bytes(), session.service.clock.now
    for n in range(5):
        for op, args in [('snapshot', {}), ('events', {'cursor': 0, 'limit': 256})]:
            ack = session.handle(dict(version=1, run_id='passive', command_id=f'{op}.{n}', operation=op, args=args))
            assert ack['status'] == 'accepted'
    assert before == (session.service.history.canonical_bytes(), session.service.clock.now)
    assert all(t['status'] == 'pending' for t in session.snapshot()['transfers'])
    assert not session.snapshot()['proposals']


def test_prepared_agent_profiles_are_distinct_and_real():
    session = preview.prepare('profiles')
    # Same public service start interface for human and three authored profiles.
    session.service.start('agent.assure', command_id='probe.assurance.work')
    while len(session.service.proposals) < 4:
        session.service.step()
    assert {p.actor_id for p in session.service.proposals} == {'jin', 'agent.build', 'agent.investigate', 'agent.assure'}
    assert session.service.clock.now > 0


def test_bootstrap_cleans_child_and_server_on_missing_projection_and_child_failure(monkeypatch, capsys):
    # Owned lifecycle is testable without pretending this fake is live/socket evidence.
    session = preview.prepare('owned')
    for server_failure, child_failure in ((False, False), (False, True), (True, False)):
        state = {'closed': False, 'terminated': False, 'waited': False}
        class Server:
            server_address = ('127.0.0.1', 12345)
            def handle_request(self): pass
            def server_close(self): state['closed'] = True
        class Child:
            pid = 123
            stdout = io.StringIO()
            def poll(self): return 1 if child_failure else None
            def terminate(self): state['terminated'] = True
            def wait(self, timeout): state['waited'] = True
        class Selector:
            def register(self, *_): pass
            def select(self, **_): return []
            def close(self): pass
        def create(*_, **__):
            if server_failure: raise PermissionError('socket denied')
            return Server()
        monkeypatch.setattr(preview, 'prepare', lambda *_: session)
        monkeypatch.setattr(preview, 'create_server', create)
        monkeypatch.setattr(preview.subprocess, 'Popen', lambda *_args, **_kwargs: Child())
        monkeypatch.setattr(preview.selectors, 'DefaultSelector', Selector)
        monkeypatch.setattr(preview.signal, 'signal', lambda *_: None)
        monkeypatch.setattr(preview.time, 'monotonic', iter([0.0, 13.0]).__next__)
        monkeypatch.setattr(sys, 'argv', ['live_preview.py', '--duration', '12'])
        with pytest.raises((RuntimeError, PermissionError)):
            preview.main()
        if not server_failure:
            assert state['closed']
            if not child_failure:
                assert state['terminated'] and state['waited']
        assert 'cleanup complete' in capsys.readouterr().out


@pytest.mark.parametrize("duration", [0, 12])
def test_default_preview_stays_open_until_its_window_closes(monkeypatch, capsys, duration):
    # Fake lifecycle only: no desktop or network acceptance claim.
    state = {'handled': 0, 'closed': False, 'polls': 0}
    class Server:
        server_address = ('127.0.0.1', 12345)
        def handle_request(self): state['handled'] += 1
        def server_close(self): state['closed'] = True
    class Child:
        pid = 123
        stdout = io.StringIO()
        def poll(self):
            state['polls'] += 1
            return None if state['polls'] == 1 else 0
    class Selector:
        def register(self, *_): pass
        def select(self, **_): return []
        def close(self): pass
    monkeypatch.setattr(preview, 'create_server', lambda *_args, **_kw: Server())
    monkeypatch.setattr(preview.subprocess, 'Popen', lambda *_args, **_kw: Child())
    monkeypatch.setattr(preview.selectors, 'DefaultSelector', Selector)
    monkeypatch.setattr(preview.signal, 'signal', lambda *_: None)
    times = iter([0.0, 1000.0])
    monkeypatch.setattr(preview.time, 'monotonic', lambda: next(times, 1000.0))
    monkeypatch.setattr(sys, 'argv', ['live_preview.py', '--duration', str(duration)])
    if duration:
        with pytest.raises(RuntimeError):
            preview.main()
        assert state['handled'] == 0
    else:
        preview.main()
        assert state['handled'] == 1  # default does not expire at the old 60 seconds
    assert state['closed']
    assert 'cleanup complete' in capsys.readouterr().out
