"""Author or verify the predeclared AE-005 toy channel experiment."""

import argparse
from dataclasses import asdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.communication import Channel, Communication, DistortionRule
from agent_empires.simulation.events import EventHistory, canonical_json
from agent_empires.simulation.knowledge import HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore
from agent_empires.simulation.randomness import NamedRandomness, RNG_SCHEME


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUTS = ("results.json", "traces.json", "run-manifest.json")
SEEDS = list(range(32))
PROFILES = {"control": (0, 0), "full_loss": (1, 0), "full_distortion": (0, 1),
            "mixed": (0.25, 0.5), "high_loss": (0.75, 0.5)}
RULE = DistortionRule("declines", "do not retry hard declines", "retry all declines")
PARAMETERS = [
    {"parameter_id": "capacity", "unit": "one-holding messages admitted per tick", "range": "integer >= 1",
     "values": [1, 4], "rationale": "single-hop congestion tests and four-message seed batches"},
    {"parameter_id": "latency", "unit": "simulation ticks", "range": "integer >= 1",
     "values": [1, 2], "rationale": "contrasting fast direct and slow two-hop routes"},
    {"parameter_id": "loss_probability", "unit": "probability per admitted message", "range": "[0,1]",
     "values": [0, 0.25, 0.75, 1], "rationale": "boundary and sensitivity controls"},
    {"parameter_id": "distortion_probability", "unit": "probability conditional on surviving loss", "range": "[0,1]",
     "values": [0, 0.5, 1], "rationale": "unchanged and defined-alternative controls"},
    {"parameter_id": "connection_cost", "unit": "resource units once per edge", "range": "integer >= 0",
     "values": [0, 1, 6], "rationale": "positive costs expose the cost of unused extra links"},
    {"parameter_id": "transfer_cost", "unit": "resource units per admitted message", "range": "integer >= 0",
     "values": [1, 4], "rationale": "cheap and expensive routes without a scalar utility"},
    {"parameter_id": "trust", "unit": "metadata score", "range": "[0,1]",
     "values": [0.5], "rationale": "neutral recorded metadata; no reliability or belief effect"},
]


def setup(run_id, seed, *, reverse=False, all_agents=False):
    history, clock, rng = EventHistory(run_id), SimulationClock(), NamedRandomness(seed)
    actors = [Actor(a, "agent" if all_agents else "human", "team") for a in "abc"]
    store = KnowledgeStore(history, reversed(actors) if reverse else actors)
    item = KnowledgeItem("policy", 1, RULE.topic, RULE.original)
    store.register_item(item)
    store.record_holding(KnowledgeHolding("initial", item.ref, HolderRef("actor", "a"),
                                         ("incident-1",), "low", "stale"),
                         tick=0, command_id="setup", correlation_id="experiment")
    return Communication(store, clock, history, rng), store, clock, history


def connect(net, channel):
    net.connect(channel, command_id=f"connect-{channel.channel_id}", correlation_id="experiment")


def send(net, channel, command, holding="initial"):
    net.send(channel, holding, command_id=command, correlation_id="experiment")


def drain(net, clock):
    while clock.pending_count:
        net.deliver(clock.pop_next())


def seeded_run(profile, seed, **controls):
    net, store, clock, history = setup(f"ae005-{profile}-{seed}", seed, **controls)
    loss, distortion = PROFILES[profile]
    connect(net, Channel("ab", "a", "b", 2, 4, loss, distortion, RULE))
    for index in range(4):
        send(net, "ab", f"message-{index}")
    assert store.view_for("b").entries == ()
    drain(net, clock)
    events = history.events
    delivered = [e for e in events if e.event_type == "KnowledgeTransferred"]
    lost = [e for e in events if e.event_type == "InformationLost"]
    distorted = [e for e in events if e.event_type == "InformationDistorted"]
    assert len(delivered) + len(lost) == 4
    assert len(distorted) <= len(delivered)
    assert net.total_cost == 4 and clock.now == 2
    assert len(store.view_for("b").entries) == len(delivered)
    assert all(e.holding.source_ids == ("incident-1",) and e.holding.confidence == "low"
               for e in store.view_for("b").entries)
    if profile == "control":
        assert len(delivered) == 4 and not distorted
    elif profile == "full_loss":
        assert len(lost) == 4 and not distorted
    elif profile == "full_distortion":
        assert len(distorted) == 4
    messages = [{"command_id": e.command_id, "tick": e.tick, "outcome": e.event_type,
                 "distorted": e.payload.get("distorted", False),
                 "loss_draw": e.payload["loss_draw"], "distortion_draw": e.payload["distortion_draw"]}
                for e in events if e.event_type in ("KnowledgeTransferred", "InformationLost")]
    result = {"profile": profile, "seed": seed, "delivered": len(delivered), "lost": len(lost),
              "distorted": len(distorted), "total_cost": net.total_cost, "messages": messages,
              "history_sha256": hashlib.sha256(history.canonical_bytes()).hexdigest()}
    return result, history.canonical_bytes()


def topology_run(topology, **controls):
    net, store, clock, history = setup(f"ae005-{topology}", 0, **controls)
    fast = Channel("ac", "a", "c", 1, 1, connection_cost=6, transfer_cost=4)
    cheap = (Channel("ab", "a", "b", 2, 1, connection_cost=1, transfer_cost=1),
             Channel("bc", "b", "c", 2, 1, connection_cost=1, transfer_cost=1))
    if topology in ("direct", "union"):
        connect(net, fast)
    if topology in ("chain", "union"):
        for channel in cheap:
            connect(net, channel)
    if topology in ("direct", "union"):
        send(net, "ac", "direct")
        drain(net, clock)
    elif topology == "chain":
        send(net, "ab", "first-hop")
        drain(net, clock)
        assert store.view_for("c").entries == ()
        send(net, "bc", "second-hop", store.view_for("b").entries[0].holding.holding_id)
        drain(net, clock)
    elif topology != "isolated":
        raise ValueError(topology)
    accessible = bool(store.view_for("c").entries)
    result = {"topology": topology, "recipient_access": accessible,
              "arrival_tick": clock.now if accessible else None, "total_cost": net.total_cost,
              "deadline_1_budget_10": accessible and clock.now <= 1 and net.total_cost <= 10,
              "deadline_4_budget_4": accessible and clock.now <= 4 and net.total_cost <= 4}
    return result, history.canonical_bytes()


def generate(output_dir):
    if platform.python_implementation() != "CPython" or sys.version_info[:3] != (3, 12, 13):
        raise RuntimeError("experiment requires CPython 3.12.13")
    if any((output_dir / name).exists() for name in OUTPUTS):
        raise ValueError("evidence exists; use --verify-against or fresh output files")
    runs, traces, summaries = [], {}, {}
    for profile in PROFILES:
        group = []
        for seed in SEEDS:
            result, history = seeded_run(profile, seed)
            assert (result, history) == seeded_run(profile, seed)
            assert (result, history) == seeded_run(profile, seed, reverse=True, all_agents=True)
            runs.append(result)
            group.append(result)
            if seed == 0:
                traces[profile] = json.loads(history)
        summaries[profile] = {
            metric: {"total": sum(r[metric] for r in group),
                     "mean_per_run": sum(r[metric] for r in group) / len(group),
                     "min_per_run": min(r[metric] for r in group),
                     "max_per_run": max(r[metric] for r in group)}
            for metric in ("delivered", "lost", "distorted")
        }
    # Paired per-message draws: higher loss cannot rescue a lost message here.
    for seed in SEEDS:
        low = next(r for r in runs if r["profile"] == "mixed" and r["seed"] == seed)
        high = next(r for r in runs if r["profile"] == "high_loss" and r["seed"] == seed)
        assert high["lost"] >= low["lost"]
        assert [(m["loss_draw"], m["distortion_draw"]) for m in low["messages"]] == [
            (m["loss_draw"], m["distortion_draw"]) for m in high["messages"]]
    topologies = []
    for topology in ("isolated", "direct", "chain", "union"):
        result, history = topology_run(topology)
        assert (result, history) == topology_run(topology, reverse=True, all_agents=True)
        topologies.append(result)
        traces[topology] = json.loads(history)
    assert [(r["arrival_tick"], r["total_cost"]) for r in topologies] == [
        (None, 0), (1, 10), (4, 4), (1, 12)]
    results = {"runs": runs, "summaries": summaries, "topologies": topologies,
               "failed_invariant_seeds": [],
               "negative_findings": [
                   "The isolated topology costs nothing but never transfers knowledge.",
                   "The union pays for unused connections and is dominated by the direct edge in this workload.",
                   "Copied and distorted messages retain one source and low confidence, even after repeated delivery.",
                   "Congestion is rejected, not buffered; retries and route choice remain explicit caller actions.",
                   "These independently sampled failures do not test correlated outages or player comprehension."]}
    paths = ["pyproject.toml", "uv.lock", "src/agent_empires/simulation/actors.py",
             "src/agent_empires/simulation/knowledge.py", "src/agent_empires/simulation/events.py",
             "src/agent_empires/simulation/clock.py", "src/agent_empires/simulation/randomness.py",
             "src/agent_empires/simulation/communication.py", "tests/unit/test_communication.py",
             "research/experiments/AE-005/protocol.md", "research/experiments/AE-005/channel_experiment.py"]
    manifest = {
        "model_version": "ae005-one-hop-v2-causal-ancestry", "scenario_version": "authored-channel-fixture-v1",
        "seed_set": SEEDS, "rng_scheme": RNG_SCHEME,
        "stream_key": ["communication-v1", "send command ID", "loss or distortion"],
        "seeded_profiles": {p: {"loss_probability": v[0], "distortion_probability": v[1]}
                            for p, v in PROFILES.items()},
        "initial_state": {"tick": 0, "actors": ["a", "b", "c"], "team": "team",
                          "holder": "a", "holding": "initial", "item": "policy@1",
                          "sources": ["incident-1"], "confidence": "low", "freshness": "stale"},
        "ordered_seeded_commands": ["setup", "connect-ab"] + [f"message-{i}" for i in range(4)],
        "topology_commands": {"isolated": ["setup"],
                              "direct": ["setup", "connect-ac", "direct"],
                              "chain": ["setup", "connect-ab", "connect-bc", "first-hop", "second-hop"],
                              "union": ["setup", "connect-ac", "connect-ab", "connect-bc", "direct"]},
        "parameters": [{**p, "assumption_id": "MA-04", "classification": "toy_gameplay",
                        "source": "invented for experiment", "calibration_version": None,
                        "uncertainty": "no empirical calibration",
                        "alternatives": "buffered service, correlated failures, ongoing connection costs",
                        "review_activity": "AE-018"} for p in PARAMETERS],
        "distortion_rule": asdict(RULE),
        "controls": ["repeat canonical history", "reverse roster registration with all-agent relabeling",
                     "paired per-message loss/distortion draws across sensitivity cases"],
        "runtime": {"implementation": platform.python_implementation(), "python": platform.python_version(),
                    "pytest": version("pytest")},
        "source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in zip(OUTPUTS, (results, traces, manifest)):
        (output_dir / name).write_bytes(canonical_json(data) + b"\n")
    return summaries, topologies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output-dir", type=Path)
    modes.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.output_dir is not None:
        summaries, topologies = generate(args.output_dir)
        print(json.dumps({"summaries": summaries, "topologies": topologies}, indent=2))
    else:
        with TemporaryDirectory(prefix="ae005-channels-") as temporary:
            fresh = Path(temporary)
            generate(fresh)
            for name in OUTPUTS:
                if (fresh / name).read_bytes() != (args.verify_against / name).read_bytes():
                    raise ValueError(f"experiment evidence differs: {name}")
        print("PASS: 160 seeded cases and four topologies reproduced; bound evidence unchanged")


if __name__ == "__main__":
    main()
