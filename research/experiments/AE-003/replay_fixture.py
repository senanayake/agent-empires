"""Author or verify the bounded AE-003 engineering fixture; no gameplay rules."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory

from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.events import CausalLink, EntityRef, EventHistory, canonical_json
from agent_empires.simulation.randomness import NamedRandomness, RNG_SCHEME


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL_VERSION = "ae003-primitives-v1"


def load_fixture():
    return json.loads((HERE / "commands.json").read_bytes())


def replay(fixture, seed, *, split_advancement=False, unrelated_draws=0):
    clock = SimulationClock(fixture["initial_state"]["tick"])
    history = EventHistory(f"{fixture['scenario_id']}-seed-{seed}")
    rng = NamedRandomness(seed)
    for _ in range(unrelated_draws):
        rng.stream("actor/policy").random()
    commands = {command["command_id"]: command for command in fixture["commands"]}
    assert len(commands) == len(fixture["commands"])
    assert [c["sequence"] for c in fixture["commands"]] == list(range(len(commands)))
    for command in fixture["commands"]:
        clock.schedule(command["tick"], command["command_id"], priority=command["priority"])
    previous = None
    for tick in sorted(command["tick"] for command in fixture["commands"]):
        if split_advancement:
            for intermediate in range(clock.now, tick + 1):
                clock.advance_to(intermediate)
        work = clock.pop_next()
        command = commands[work.command_id]
        samples = [rng.stream("world/workload").randrange(1_000_000)
                   for _ in range(command["sample_count"])]
        parents = [] if previous is None else [CausalLink(previous.event_id, "direct_cause")]
        previous = history.append(
            tick=clock.now, event_type="FixtureSampled", schema_version=1,
            command_id=work.command_id, correlation_id="fixture-sequence-1",
            entities=[EntityRef("fixture", fixture["scenario_id"], 1)], parents=parents,
            payload={"samples": samples, "stream": "world/workload",
                     "command_sequence": command["sequence"]},
        )
    assert clock.pending_count == 0
    return history.canonical_bytes()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = [ROOT / "pyproject.toml", ROOT / "uv.lock", HERE / "commands.json",
             HERE / "protocol.md", Path(__file__).resolve()]
    paths += sorted((ROOT / "src/agent_empires").rglob("*.py"))
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def generate(output_dir):
    if platform.python_implementation() != "CPython" or sys.version_info[:3] != (3, 12, 13):
        raise RuntimeError("fixture evidence requires CPython 3.12.13")
    fixture = load_fixture()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1, "model_version": MODEL_VERSION,
        "source_hashes": source_hashes(),
        "scenario_id": fixture["scenario_id"], "scenario_version": fixture["scenario_version"],
        "fixture_sha256": sha(HERE / "commands.json"),
        "initial_state": fixture["initial_state"], "commands": fixture["commands"],
        "seeds": fixture["seeds"], "rng_scheme": RNG_SCHEME,
        "rng_streams": ["world/workload", "actor/policy"],
        "queue_order": ["tick", "priority", "insertion_seq"],
        "runtime": {"implementation": platform.python_implementation(),
                    "python": platform.python_version(), "platform": platform.platform(),
                    "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
                    "dependencies": {name: version(name) for name in
                                     ("pytest", "iniconfig", "packaging", "pluggy", "pygments")}},
    }
    results = {"schema_version": 1, "runs": [], "failed_seeds": []}
    sample_sets = []
    for seed in fixture["seeds"]:
        raw = replay(fixture, seed)
        assert raw == replay(fixture, seed)
        assert raw == replay(fixture, seed, split_advancement=True)
        assert raw == replay(fixture, seed, unrelated_draws=100)
        name = f"history-seed-{seed}.json"
        (output_dir / name).write_bytes(raw)
        history = json.loads(raw)
        sample_sets.append([e["payload"]["samples"] for e in history["events"]])
        results["runs"].append({"seed": seed, "history": name,
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "event_count": len(history["events"]),
                                "repeat_identical": True, "split_advancement_identical": True,
                                "unrelated_stream_identical": True})
    assert sample_sets[0] != sample_sets[1]
    results["different_seeds_change_samples"] = True
    # Retain the negative counterexample: names do not isolate draws within a stream.
    base, shifted = NamedRandomness(17).stream("world/workload"), NamedRandomness(17).stream("world/workload")
    baseline = [base.randrange(1_000_000) for _ in range(5)]
    shifted.randrange(1_000_000)
    shifted_samples = [shifted.randrange(1_000_000) for _ in range(4)]
    assert shifted_samples == baseline[1:] and shifted_samples != baseline[:4]
    results["same_stream_shift_counterexample"] = {
        "seed": 17, "baseline": baseline, "after_extra_draw": shifted_samples,
        "limitation": "Extra draws within the same named stream shift counterfactual samples."}
    (output_dir / "run-manifest.json").write_bytes(canonical_json(manifest) + b"\n")
    (output_dir / "results.json").write_bytes(canonical_json(results) + b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-seed", type=int)
    mode.add_argument("--output-dir", type=Path)
    mode.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.emit_seed is not None:
        sys.stdout.buffer.write(replay(load_fixture(), args.emit_seed))
    elif args.output_dir is not None:
        names = ["run-manifest.json", "results.json"] + [
            f"history-seed-{seed}.json" for seed in load_fixture()["seeds"]]
        if any((args.output_dir / name).exists() for name in names):
            raise ValueError("evidence already exists; use --verify-against or a fresh output directory")
        generate(args.output_dir)
        print("PASS: authored fixture seeds 17 and 23 with controls and retained RNG counterexample")
    else:
        with TemporaryDirectory(prefix="ae003-replay-") as temporary:
            fresh = Path(temporary)
            generate(fresh)
            for path in sorted(fresh.iterdir()):
                if path.read_bytes() != (args.verify_against / path.name).read_bytes():
                    raise ValueError(f"replay evidence differs: {path.name}")
        print("PASS: canonical histories, controls, source hashes and run manifest reproduced; evidence unchanged")


if __name__ == "__main__":
    main()
