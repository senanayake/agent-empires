import pytest

from agent_empires.simulation.clock import SimulationClock


def test_order_is_tick_then_priority_then_insertion_not_command_id():
    clock = SimulationClock()
    scheduled = [
        clock.schedule(8, "later", priority=-100),
        clock.schedule(3, "z-first"),
        clock.schedule(3, "a-second"),
        clock.schedule(3, "priority", priority=-1),
    ]
    assert [work.insertion_seq for work in scheduled] == [0, 1, 2, 3]
    assert clock.now == 0
    assert [clock.pop_next().command_id for _ in scheduled] == [
        "priority", "z-first", "a-second", "later"
    ]
    assert clock.now == 8
    assert clock.pending_count == 0
    assert clock.pop_next() is None
    assert clock.now == 8


def test_dynamic_equal_time_work_joins_pending_queue():
    clock = SimulationClock()
    clock.schedule(0, "first")
    clock.schedule(0, "already-pending")
    assert clock.pop_next().command_id == "first"
    clock.schedule(0, "new-peer")
    clock.schedule(0, "new-priority", priority=-1)
    assert [clock.pop_next().command_id for _ in range(3)] == [
        "new-priority", "already-pending", "new-peer"
    ]


def test_advancement_cannot_skip_pending_work_or_reverse_time():
    clock = SimulationClock()
    clock.schedule(5, "due")
    clock.advance_to(5)
    assert clock.now == 5
    for tick in (4, 6):
        with pytest.raises(ValueError):
            clock.advance_to(tick)
        assert clock.now == 5
        assert clock.pending_count == 1
    clock.pop_next()
    clock.advance_to(10**30)
    assert clock.now == 10**30


@pytest.mark.parametrize("bad", [-1, 1.0, True, False, "1", None])
def test_invalid_ticks_never_change_state(bad):
    with pytest.raises((TypeError, ValueError), match="tick"):
        SimulationClock(start_tick=bad)
    clock = SimulationClock()
    for action in (lambda: clock.schedule(bad, "invalid"), lambda: clock.advance_to(bad)):
        with pytest.raises((TypeError, ValueError), match="tick"):
            action()
        assert clock.now == 0
        assert clock.pending_count == 0
    assert clock.schedule(0, "valid").insertion_seq == 0


def test_past_scheduling_and_invalid_priority_fail_without_consuming_sequence():
    clock = SimulationClock(start_tick=7)
    with pytest.raises(ValueError, match="past"):
        clock.schedule(6, "past")
    for priority in (True, 0.5, "0", None):
        with pytest.raises(TypeError, match="priority"):
            clock.schedule(7, "bad-priority", priority=priority)
    for command_id in ("", " ", 7, None):
        with pytest.raises((TypeError, ValueError), match="command_id"):
            clock.schedule(7, command_id)
    work = clock.schedule(7, "now")
    assert work.insertion_seq == 0
    with pytest.raises(AttributeError):
        work.tick = 4
    with pytest.raises(AttributeError):
        clock.now = 4


def test_queue_matches_sorted_reference_for_many_ties():
    clock = SimulationClock()
    expected = []
    for i in range(150):
        tick, priority = (i * 7) % 11, (i * 3) % 5 - 2
        work = clock.schedule(tick, f"command-{i}", priority=priority)
        expected.append((tick, priority, i, work.command_id))
    actual = []
    while clock.pending_count:
        work = clock.pop_next()
        actual.append((clock.now, work.priority, work.insertion_seq, work.command_id))
    assert actual == sorted(expected)
