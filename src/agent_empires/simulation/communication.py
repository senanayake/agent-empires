"""Explicit directed, capacity-limited transfers of accessible holding snapshots.

One message carries one holding. Capacity is admissions per integer tick (no
backlog); latency is positive ticks, with pipelined messages allowed. Costs are
integer toy resource units, charged at connection and admission, never refunded.
Trust is metadata. Forwarding requires another command, not graph-wide access.

Use the same store/history/clock for one single-consumer run. The caller pops
scheduled work and dispatches it to deliver; this owner never drains other work.
The ``communication:`` item/holding/queued-command namespace is reserved here.
The trusted owner/audit are not actor interfaces. Give policies fresh store views.
"""

from dataclasses import asdict, dataclass
import math

from .actors import require_text
from .clock import ScheduledCommand, SimulationClock
from .events import CausalLink, EntityRef, Event, EventHistory, canonical_json
from .knowledge import HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore, KnownProposition
from .randomness import NamedRandomness


def _integer(value: int, field: str, minimum: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer (not bool)")
    if value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")


def _probability(value: float, field: str) -> None:
    if type(value) not in (int, float):
        raise TypeError(f"{field} must be numeric (not bool)")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{field} must be finite and in [0, 1]")


@dataclass(frozen=True, slots=True)
class DistortionRule:
    """An authored syntactic replacement, not a semantic or truth evaluation."""

    topic: str
    original: str
    alternative: str

    def __post_init__(self) -> None:
        for field in ("topic", "original", "alternative"):
            require_text(getattr(self, field), field)
        if self.original == self.alternative:
            raise ValueError("distortion must change the proposition")


@dataclass(frozen=True, slots=True)
class Channel:
    channel_id: str
    sender: str
    recipient: str
    latency: int
    capacity: int
    loss_probability: float = 0.0
    distortion_probability: float = 0.0
    distortion: DistortionRule | None = None
    transfer_cost: int = 1
    connection_cost: int = 0
    trust: float = 0.5

    def __post_init__(self) -> None:
        for field in ("channel_id", "sender", "recipient"):
            require_text(getattr(self, field), field)
        if self.sender == self.recipient:
            raise ValueError("a channel requires distinct endpoints")
        for field in ("latency", "capacity"):
            _integer(getattr(self, field), field, 1)
        for field in ("transfer_cost", "connection_cost"):
            _integer(getattr(self, field), field, 0)
        for field in ("loss_probability", "distortion_probability", "trust"):
            _probability(getattr(self, field), field)
        if self.distortion is not None and type(self.distortion) is not DistortionRule:
            raise TypeError("distortion must be a DistortionRule")
        if self.distortion_probability > 0 and self.distortion is None:
            raise ValueError("positive distortion probability requires a defined rule")


@dataclass(frozen=True, slots=True)
class _Transfer:
    work: ScheduledCommand
    channel: Channel
    source: KnownProposition
    sent: Event


class Communication:
    """One-hop transmission owner; no implicit truth, trust or routing policy.

    Admission snapshots current source access. Sender departure/revocation later
    cannot recall that snapshot. Recipient departure before arrival instead emits
    InformationLost. Departures are read from the shared authoritative history;
    AE-004's public view deliberately does not distinguish empty from departed.
    """

    def __init__(self, store: KnowledgeStore, clock: SimulationClock,
                 history: EventHistory, randomness: NamedRandomness) -> None:
        self._store, self._clock, self._history, self._rng = store, clock, history, randomness
        self._channels: dict[str, tuple[Channel, Event]] = {}
        self._retired: set[str] = set()
        self._usage: dict[str, tuple[int, int]] = {}
        self._commands: set[str] = set()
        self._pending: dict[str, _Transfer] = {}
        self._total_cost = 0

    @property
    def total_cost(self) -> int:
        return self._total_cost

    @property
    def channels(self) -> tuple[Channel, ...]:
        """Active directed edges only; retired IDs and admitted snapshots persist."""
        return tuple(c for key, (c, _) in self._channels.items() if key not in self._retired)

    def handles(self, work: ScheduledCommand) -> bool:
        return work.command_id in self._pending

    def retire_actor(self, actor_id: str, *, command_id: str, correlation_id: str,
                     parents: tuple[CausalLink, ...] = ()) -> tuple[Event, ...]:
        """Disable all incident edges without recalling or refunding sent messages."""
        self._store.actor_for(actor_id)
        events = []
        for channel in self.channels:
            if actor_id not in (channel.sender, channel.recipient):
                continue
            connected = self._channels[channel.channel_id][1]
            event = self._history.append(
                tick=self._clock.now, event_type="ChannelRetired", command_id=command_id,
                correlation_id=correlation_id,
                entities=(EntityRef("channel", channel.channel_id, 2),),
                parents=parents + (CausalLink(connected.event_id, "direct_cause"),),
                payload={"channel_id": channel.channel_id, "actor_id": actor_id},
            )
            self._retired.add(channel.channel_id)
            events.append(event)
        return tuple(events)

    def _present(self, actor_id: str) -> bool:
        return self._store.is_present(actor_id)

    def connect(self, channel: Channel, *, command_id: str, correlation_id: str,
                parents: tuple[CausalLink, ...] = ()) -> Event:
        if type(channel) is not Channel:
            raise TypeError("expected Channel")
        if channel.channel_id in self._channels:
            raise ValueError("duplicate channel")
        if not self._present(channel.sender) or not self._present(channel.recipient):
            raise ValueError("channel endpoints must be present")
        event = self._history.append(
            tick=self._clock.now, event_type="ChannelConnected", command_id=command_id,
            correlation_id=correlation_id, parents=parents,
            entities=(EntityRef("channel", channel.channel_id, 1),),
            payload={"channel": asdict(channel), "cost": channel.connection_cost},
        )
        self._channels[channel.channel_id] = channel, event
        self._total_cost += channel.connection_cost
        return event

    def send(self, channel_id: str, holding_id: str, *, command_id: str,
             correlation_id: str, parents: tuple[CausalLink, ...] = ()) -> ScheduledCommand:
        require_text(command_id, "command_id")
        if command_id in self._commands:
            raise ValueError("duplicate send command")
        if channel_id not in self._channels or channel_id in self._retired:
            raise ValueError("unknown directed channel")
        channel, connected = self._channels[channel_id]
        if not self._present(channel.sender) or not self._present(channel.recipient):
            raise ValueError("transfer endpoints must be present")
        source = next((entry for entry in self._store.view_for(channel.sender).entries
                       if entry.holding.holding_id == holding_id), None)
        if source is None:
            raise ValueError("sender has no accessible holding with that ID")
        rule = channel.distortion
        if channel.distortion_probability > 0 and (
                source.item.topic != rule.topic or source.item.proposition != rule.original):
            raise ValueError("no defined distortion rule for this proposition")
        tick, count = self._usage.get(channel_id, (self._clock.now, 0))
        used = count if tick == self._clock.now else 0
        if used >= channel.capacity:
            raise ValueError("channel capacity exhausted for this tick")
        if type(parents) is not tuple or any(type(p) is not CausalLink for p in parents):
            raise TypeError("parents must be a tuple of CausalLink")
        # Acquisition and current permission are distinct causes. A completed
        # transfer includes distortion evidence that its storage fact alone
        # cannot explain. Access revisions must not replace that acquisition.
        acquisition = next(e for e in reversed(self._history.events)
                           if e.event_type in ("KnowledgeTransferred", "KnowledgeHoldingRecorded")
                           and any(ref.entity_type == "knowledge_holding"
                                   and ref.entity_id == source.holding.holding_id
                                   for ref in e.entities))
        access = next(e for e in reversed(self._history.events)
                      if e.event_type in ("KnowledgeHoldingRecorded", "HoldingAccessChanged")
                      and source.holding.ref in e.entities)
        lineage = tuple(dict.fromkeys(
            CausalLink(event.event_id, "direct_cause")
            for event in (acquisition, access, connected)
        ))
        combined = parents + tuple(link for link in lineage if link not in parents)
        event = self._history.append(
            tick=self._clock.now, event_type="TransferSent", command_id=command_id,
            correlation_id=correlation_id, parents=combined,
            entities=(EntityRef("channel", channel_id, 1), source.item.ref, source.holding.ref),
            payload={"channel_id": channel_id, "sender": channel.sender,
                     "recipient": channel.recipient, "source_holding": source.holding.ref.as_dict(),
                     "source_ids": list(source.holding.source_ids), "units": 1,
                     "cost": channel.transfer_cost, "delivery_tick": self._clock.now + channel.latency},
        )
        # Following append, only generated valid data is used; no caller callback.
        work = self._clock.schedule(self._clock.now + channel.latency,
                                    f"communication:{event.event_id}")
        self._pending[work.command_id] = _Transfer(work, channel, source, event)
        self._commands.add(command_id)
        self._usage[channel_id] = self._clock.now, used + 1
        self._total_cost += channel.transfer_cost
        return work

    def deliver(self, work: ScheduledCommand) -> tuple[Event, ...]:
        """Resolve once, at its scheduled tick, after caller pop_next().

        Loss and distortion use separate per-command named streams. A lost
        message cannot be distorted or delivered. HoldingRecorded establishes
        acquisition first; the outcome fact then cites it and any distortion
        fact. All these facts share the same simulated arrival tick.
        """
        if type(work) is not ScheduledCommand:
            raise TypeError("expected ScheduledCommand")
        transfer = self._pending.get(work.command_id)
        if transfer is None or transfer.work != work or self._clock.now != work.tick:
            raise ValueError("unknown, completed or not-due transfer")
        if self._history.events and self._history.events[-1].tick > work.tick:
            raise ValueError("history is ahead of the delivery tick")
        channel, source, sent = transfer.channel, transfer.source, transfer.sent
        base = {"channel_id": channel.channel_id, "sender": channel.sender,
                "recipient": channel.recipient, "source_holding": source.holding.ref.as_dict(),
                "source_ids": list(source.holding.source_ids)}
        causal = (CausalLink(sent.event_id, "direct_cause"),)

        def fact(kind: str, payload: dict, *, parents=causal, entities=()) -> Event:
            return self._history.append(
                tick=work.tick, event_type=kind, command_id=sent.command_id,
                correlation_id=sent.correlation_id, parents=parents, entities=entities,
                payload={**base, **payload},
            )

        def draw(purpose: str) -> float:
            name = canonical_json(["communication-v1", sent.command_id, purpose]).decode("ascii")
            return self._rng.stream(name).random()

        if not self._present(channel.recipient):
            departure = next(e for e in reversed(self._history.events)
                             if e.event_type == "ActorDeparted"
                             and e.payload["actor_id"] == channel.recipient)
            events = (fact("InformationLost", {"reason": "recipient_unavailable"},
                           parents=causal + (CausalLink(departure.event_id, "direct_cause"),)),)
        else:
            loss_draw, distortion_draw = draw("loss"), draw("distortion")
            samples = {"loss_draw": loss_draw, "distortion_draw": distortion_draw}
            if loss_draw < channel.loss_probability:
                events = (fact("InformationLost", {"reason": "channel_loss", **samples}),)
            else:
                distorted = distortion_draw < channel.distortion_probability
                item = source.item
                if distorted:
                    item = KnowledgeItem(f"communication:{sent.event_id}:distorted", 1,
                                         source.item.topic, channel.distortion.alternative)
                    self._store.register_item(item)
                holding = KnowledgeHolding(
                    f"communication:{sent.event_id}:holding", item.ref,
                    HolderRef("actor", channel.recipient), source.holding.source_ids,
                    source.holding.confidence, source.holding.freshness, source.holding.explicit,
                )
                recorded = self._store.record_holding(
                    holding, tick=work.tick, command_id=sent.command_id,
                    correlation_id=sent.correlation_id, parents=causal,
                )
                acquired = [recorded]
                if distorted:
                    acquired.append(fact(
                        "InformationDistorted",
                        {"original_item": source.item.ref.as_dict(), "received_item": item.ref.as_dict(),
                         "original_proposition": source.item.proposition,
                         "received_proposition": item.proposition, **samples},
                        entities=(source.item.ref, item.ref),
                    ))
                acquired.append(fact(
                    "KnowledgeTransferred",
                    {"received_holding": holding.ref.as_dict(), "distorted": distorted, **samples},
                    parents=causal + tuple(CausalLink(e.event_id, "direct_cause") for e in acquired),
                    entities=(item.ref, holding.ref),
                ))
                events = tuple(acquired)
        del self._pending[work.command_id]
        return events
