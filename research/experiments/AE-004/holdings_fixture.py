"""Author or verify AE-004's deterministic three-holder fixture without overwrites."""

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
from agent_empires.simulation.events import EntityRef, EventHistory, canonical_json
from agent_empires.simulation.knowledge import (
    Artifact, HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUTS = ("results.json", "history.json", "run-manifest.json")


def replay(fixture, *, reverse_registration=False):
    roster = [Actor(**actor) for actor in fixture["actors"]]
    artifacts = [Artifact(a["artifact_id"], tuple(a["reader_ids"]))
                 for a in fixture["artifacts"]]
    items = [KnowledgeItem(**item) for item in fixture["items"]]
    history = EventHistory(fixture["fixture_id"])
    store = KnowledgeStore(history, reversed(roster) if reverse_registration else roster,
                           reversed(artifacts) if reverse_registration else artifacts)
    for item in reversed(items) if reverse_registration else items:
        store.register_item(item)
    for data in fixture["holdings"]:
        holding = KnowledgeHolding(
            data["holding_id"], EntityRef("knowledge_item", data["item_id"], data["item_version"]),
            HolderRef(data["holder_kind"], data["holder_id"]),
            tuple(data["source_ids"]), data["confidence"], data["freshness"],
            data["explicit"], data["accessible"],
        )
        store.record_holding(holding, tick=0, command_id=f"setup-{holding.holding_id}",
                             correlation_id="initial-holdings")

    def snapshot(label):
        views = {}
        for actor in roster:
            view = store.view_for(actor.actor_id)
            views[actor.actor_id] = {
                "entries": [{"item": asdict(e.item), "holding": e.holding.as_dict()}
                            for e in view.entries],
                "conflicting_topics": list(view.conflicting_topics),
                "source_ids": list(view.source_ids),
            }
            assert view.lookup("audit-only", 1) is None
            assert view.lookup("sealed", 1) is None
        return {"after": label, "actor_views": views,
                "organization_available": [i.ref.as_dict() for i in items
                                           if store.organization_available(i.ref)]}

    snapshots = [snapshot("setup")]
    clock = SimulationClock()
    commands = {c["command_id"]: c for c in fixture["commands"]}
    assert len(commands) == len(fixture["commands"])
    for command in fixture["commands"]:
        clock.schedule(command["tick"], command["command_id"])
    while clock.pending_count:
        work = clock.pop_next()
        store.depart_actor(commands[work.command_id]["actor_id"], tick=clock.now,
                           command_id=work.command_id, correlation_id="departures")
        snapshots.append(snapshot(work.command_id))

    results = {
        "fixture_id": fixture["fixture_id"], "fixture_version": fixture["fixture_version"],
        "snapshots": snapshots,
        "organization_losses": [e.payload for e in history.events if e.event_type == "KnowledgeLost"],
        "team_unreachability": [e.payload for e in history.events if e.event_type == "KnowledgeUnreachable"],
        "counterexamples": [
            "A surviving document cannot preserve organizational availability after its last reader departs.",
            "Three copies of policy version 1 still name just one policy-origin source.",
            "Stale high-confidence policy and a newer low-confidence alternative coexist; neither is certified true.",
        ],
    }
    assert [r["item_id"] for r in results["organization_losses"]] == ["rationale", "policy", "policy"]
    assert [r["version"] for r in results["organization_losses"]] == [1, 1, 2]
    assert snapshots[1]["actor_views"]["jin"]["conflicting_topics"] == ["decline-policy"]
    assert snapshots[2]["organization_available"] == []
    return results, history.canonical_bytes()


def generate(output_dir):
    if platform.python_implementation() != "CPython" or sys.version_info[:3] != (3, 12, 13):
        raise RuntimeError("fixture evidence requires CPython 3.12.13")
    fixture = json.loads((HERE / "holdings.json").read_bytes())
    result, history = replay(fixture)
    assert (result, history) == replay(fixture)
    assert (result, history) == replay(fixture, reverse_registration=True)
    paths = ["pyproject.toml", "uv.lock", "src/agent_empires/simulation/actors.py",
             "src/agent_empires/simulation/knowledge.py", "src/agent_empires/simulation/events.py",
             "src/agent_empires/simulation/clock.py", "tests/unit/test_knowledge.py",
             "research/experiments/AE-004/holdings.json", "research/experiments/AE-004/protocol.md",
             "research/experiments/AE-004/holdings_fixture.py"]
    manifest = {
        "model_version": "ae004-holdings-v1", "fixture_id": fixture["fixture_id"],
        "fixture_version": fixture["fixture_version"], "commands": fixture["commands"],
        "initial_tick": 0, "seeds": [], "randomness": "none; deterministic access rules",
        "controls": ["repeat replay", "reverse actor/artifact/item registration"],
        "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                    "pytest": version("pytest")},
        "source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    if any((output_dir / name).exists() for name in OUTPUTS):
        raise ValueError("evidence exists; use --verify-against or a fresh output directory")
    (output_dir / "results.json").write_bytes(canonical_json(result) + b"\n")
    (output_dir / "history.json").write_bytes(history)
    (output_dir / "run-manifest.json").write_bytes(canonical_json(manifest) + b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output-dir", type=Path)
    modes.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.output_dir is not None:
        generate(args.output_dir)
        print("PASS: three-holder fixture authored with repeated and reversed-registration controls")
    else:
        with TemporaryDirectory(prefix="ae004-holdings-") as temporary:
            fresh = Path(temporary)
            generate(fresh)
            for name in OUTPUTS:
                if (fresh / name).read_bytes() != (args.verify_against / name).read_bytes():
                    raise ValueError(f"fixture evidence differs: {name}")
        print("PASS: canonical history, results and source-bound manifest reproduced; evidence unchanged")


if __name__ == "__main__":
    main()
