"""Explicit integer time; pending work is ordered separately from recorded facts."""

from dataclasses import dataclass
import heapq


def require_tick(tick: int) -> None:
    if type(tick) is not int:
        raise TypeError("tick must be an integer (not bool)")
    if tick < 0:
        raise ValueError("tick must be nonnegative")


@dataclass(frozen=True, slots=True)
class ScheduledCommand:
    tick: int
    priority: int
    insertion_seq: int
    command_id: str


class SimulationClock:
    """Single-consumer queue ordered by (tick, priority, insertion_seq).

    Smaller priorities run first among currently pending work. Work inserted at
    the current tick cannot precede already popped work. Callers dispatch returned
    command IDs; the clock never invokes callbacks or reads wall time.
    """

    def __init__(self, start_tick: int = 0) -> None:
        require_tick(start_tick)
        self._now = start_tick
        self._next_sequence = 0
        self._queue: list[tuple[int, int, int, ScheduledCommand]] = []

    @property
    def now(self) -> int:
        return self._now

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    def schedule(self, tick: int, command_id: str, *, priority: int = 0) -> ScheduledCommand:
        require_tick(tick)
        if tick < self._now:
            raise ValueError("cannot schedule a tick in the past")
        if type(priority) is not int:
            raise TypeError("priority must be an integer (not bool)")
        if not isinstance(command_id, str):
            raise TypeError("command_id must be a string")
        if not command_id.strip():
            raise ValueError("command_id must be nonempty")
        work = ScheduledCommand(tick, priority, self._next_sequence, command_id)
        heapq.heappush(self._queue, (tick, priority, work.insertion_seq, work))
        self._next_sequence += 1
        return work

    def pop_next(self) -> ScheduledCommand | None:
        """Advance to and remove one item; an empty queue leaves time unchanged."""
        if not self._queue:
            return None
        tick, _, _, work = heapq.heappop(self._queue)
        self._now = tick
        return work

    def advance_to(self, tick: int) -> None:
        """Advance idle time, stopping at (never beyond) the earliest pending tick."""
        require_tick(tick)
        if tick < self._now:
            raise ValueError("cannot advance to a tick in the past")
        if self._queue and self._queue[0][0] < tick:
            raise ValueError("cannot skip pending work; pop it before advancing")
        self._now = tick
