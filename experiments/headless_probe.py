"""AE-007 structural probe; authored claims, no payment outcome/truth oracle.

Execute from the checkout root using its locked CPython 3.12.13 environment.
The harness dispatches existing simulation owners in process; no transport.
"""

import argparse
import ast
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import sys
import tempfile
import time

from agent_empires.simulation.actors import Actor
from agent_empires.simulation.clock import SimulationClock
from agent_empires.simulation.communication import Channel, Communication
from agent_empires.simulation.decisions import (
    AuthorityGrant, AuthorityRegistry, CapabilityProfile, DecisionQuestion,
    Decisions, EvidenceUse,
)
from agent_empires.simulation.events import EntityRef, EventHistory
from agent_empires.simulation.knowledge import (
    HolderRef, KnowledgeHolding, KnowledgeItem, KnowledgeStore,
)
from agent_empires.simulation.metrics import decision_metrics
from agent_empires.simulation.randomness import NamedRandomness, RNG_SCHEME


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (7, 19, 31)
BUDGET_SECONDS = 30
OUTPUTS = ("results.json", "run-manifest.json", "timing.json")
MODEL_VERSION = "ae007-headless-composition-v2-root-review"
OPTIONS = ("none", "one", "three")
PROFILE = CapabilityProfile(("three", "one", "none"), confidence="high")


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def check_dependency_boundary(directory):
    """Static allowlist: stdlib (excluding network/UI) or sibling simulation.

    Reject dynamic import facilities too. This checks the current source tree,
    including imports in dormant branches; it is not a hostile-code sandbox.
    """
    forbidden = {"http", "urllib", "socket", "ssl", "ftplib", "smtplib", "xmlrpc",
                 "tkinter", "turtle", "webbrowser", "importlib", "builtins"}
    paths = sorted(directory.rglob("*.py"))
    if not paths:
        raise ValueError("no simulation sources to check for imports")
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level != 1:
                        raise ValueError(f"forbidden escaping import in {path.name}")
                    names = [node.module] if node.module else [a.name for a in node.names]
                    if any(not (directory / (name.split('.')[0] + '.py')).exists()
                           for name in names):
                        raise ValueError(f"non-simulation relative import in {path.name}")
                    continue
                modules = [node.module or ""]
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"__import__", "eval", "exec"}:
                    raise ValueError(f"dynamic import/code in {path.name}")
            for module in modules:
                top = module.split('.')[0]
                sibling = module.startswith("agent_empires.simulation.") and (
                    directory / (module.split('.')[2] + '.py')).exists()
                if not sibling and (top not in sys.stdlib_module_names or top in forbidden):
                    raise ValueError(f"forbidden import {module} in {path.name}")
    return [str(path.relative_to(directory)) for path in paths]


def command(op, **args):
    return {"op": op, **args}


def strategies():
    holding = command("claim", item="rationale", actor="holder", proposition="one",
                      sources=["policy-rationale"], freshness="current")
    connect = command("connect")
    send = command("send", holding="rationale")
    deliver = command("deliver")
    depart = command("depart", actor="holder")
    infer = command("infer", missing=["rationale for retry cap"])
    root = command("grant", grant="root", actor="owner", basis="explicit_authorization",
                   options=list(OPTIONS), can_delegate=True)
    return {
        "closure": [holding, infer],
        "clarification": [holding, root, connect, send, deliver,
                          command("delegate"),
                          command("select", option="one", grant="child", rationale="received")],
        "sole_loss": [holding, depart, infer],
        "surviving": [holding, connect, send, deliver, depart, infer],
        "harmless": [infer,
                     command("claim", item="benign-window", actor="worker",
                             proposition="authored first-retry recovery; caps not compared",
                             sources=["benign-window"], freshness="current"),
                     command("select", option="three", evidence={"holding": "benign-window",
                             "subject_version": 1, "option": "three", "stance": "inconclusive"})],
        "wrong_authority": [command("grant", grant="policy", actor="worker",
                                    basis="policy_constraint", options=["none"], can_delegate=False),
                            command("select", option="none", grant="policy"),
                            command("claim", item="challenge", actor="worker",
                                    proposition="authored matched observation challenges blanket policy",
                                    sources=["independent-trial"], freshness="current"),
                            command("select", option="none", grant="policy", evidence={
                                    "holding": "challenge", "subject_version": 1,
                                    "option": "none", "stance": "challenges"}),
                            command("select", actor="owner", option="none", grant="policy",
                                    expect_rejection=True)],
    }


def replay_case(name, seed, plan, swap_kinds=False):
    history = EventHistory(name)
    actors = [Actor("worker", "human" if swap_kinds else "agent", "team"),
              Actor("holder", "agent" if swap_kinds else "human", "team"),
              Actor("owner", "agent" if swap_kinds else "human", "team")]
    store = KnowledgeStore(history, actors)
    clock = SimulationClock()
    authority = AuthorityRegistry(store, history)
    decisions = Decisions(store, authority, history)
    question = DecisionQuestion("choice", "retry_count", "work-item", OPTIONS)
    decisions.register(question)
    communication = Communication(store, clock, history, NamedRandomness(seed))
    snapshots, commands = [], []
    received = None
    tracked_item = None
    for index, raw in enumerate(plan):
        cmd = dict(raw, command_id=f"c{index:02d}")
        common = dict(tick=clock.now, command_id=cmd["command_id"], correlation_id=name)
        transport = {key: value for key, value in common.items() if key != "tick"}
        start = len(history.events)
        before = history.canonical_bytes()
        prior_versions = decisions.versions("choice")
        op = cmd["op"]
        rejected = None
        try:
            if op == "claim":
                item = KnowledgeItem(cmd["item"], 1, question.topic, cmd["proposition"])
                store.register_item(item)
                store.record_holding(KnowledgeHolding(cmd["item"], item.ref,
                    HolderRef("actor", cmd["actor"]), tuple(cmd["sources"]), "high",
                    cmd["freshness"]), **common)
                tracked_item = item.ref
            elif op == "connect":
                communication.connect(Channel("clarify", "holder", "worker", 1, 1), **transport)
            elif op == "send":
                communication.send("clarify", cmd["holding"], **transport)
            elif op == "deliver":
                work = clock.pop_next()
                if work is None:
                    raise ValueError("no pending delivery")
                cmd["scheduled_work"] = asdict(work)
                communication.deliver(work)
                received = store.view_for("worker").entries[0].holding.holding_id
            elif op == "depart":
                store.depart_actor(cmd["actor"], **common)
            elif op == "grant":
                authority.add_root(AuthorityGrant(cmd["grant"], cmd["actor"], question.scope,
                    tuple(cmd["options"]), basis=cmd["basis"], can_delegate=cmd["can_delegate"]), **common)
            elif op == "delegate":
                authority.delegate("child", "root", "owner", "worker", options=OPTIONS, **common)
            elif op == "infer":
                decisions.infer("choice", "worker", PROFILE, expected_version=len(prior_versions),
                                missing_information=tuple(cmd["missing"]), **common)
            elif op == "select":
                evidence = ()
                if "evidence" in cmd:
                    e = cmd["evidence"]
                    evidence = (EvidenceUse(e["holding"], EntityRef("decision", "choice",
                                e["subject_version"]), e["option"], e["stance"], "observation", "usable"),)
                rationale = (received,) if cmd.get("rationale") == "received" else ()
                decisions.select("choice", cmd["option"], actor_id=cmd.get("actor", "worker"),
                    expected_version=len(prior_versions), confidence="high", reason="explicit probe command",
                    grant_id=cmd.get("grant"), evidence=evidence, rationale_holding_ids=rationale, **common)
            else:
                raise ValueError(f"unknown command: {op}")
        except ValueError as exc:
            if not cmd.get("expect_rejection"):
                raise
            if before != history.canonical_bytes() or prior_versions != decisions.versions("choice"):
                raise ValueError("rejected command mutated history/decisions") from exc
            rejected = str(exc)
        else:
            if cmd.get("expect_rejection"):
                raise ValueError("expected rejection did not occur")
        cmd.update(tick=clock.now, event_sequences=list(range(start, len(history.events))))
        commands.append(cmd)
        snapshots.append({"command_id": cmd["command_id"], "op": op, "rejected": rejected,
                          "tick": clock.now, "pending_count": clock.pending_count,
                          "transfer_cost": communication.total_cost,
                          "worker_holdings": [asdict(e) for e in store.view_for("worker").entries],
                          "holder_holdings": [asdict(e) for e in store.view_for("holder").entries],
                          "item_available": tracked_item is not None and store.organization_available(tracked_item),
                          "metrics": asdict(decision_metrics(history)),
                          "decision_version": len(decisions.versions("choice"))})
    result = {"commands": commands, "snapshots": snapshots,
              "versions": [asdict(v) for v in decisions.versions("choice")],
              "metrics": asdict(decision_metrics(history)),
              "history": [e.as_dict() for e in history.events]}
    # Normalize tuples to JSON lists before exposing or comparing results.
    result = json.loads(encode(result))
    result["causal_review"] = review_causality(result)
    return result


def review_causality(case):
    """Account for every emitted fact, with external commands as explicit roots."""
    earlier, review = set(), []
    roots = {"KnowledgeHoldingRecorded": "claim", "ChannelConnected": "connect",
             "AuthorityGranted": "grant", "ActorDeparted": "depart", "DecisionSelected": "infer"}
    commands = {c["command_id"]: c for c in case["commands"]}
    dispatches = {seq: c for c in case["commands"] for seq in c["event_sequences"]}
    for event in case["history"]:
        origin = commands.get(event["command_id"])
        cmd = dispatches.get(event["sequence"])
        if origin is None or cmd is None:
            raise ValueError("event has no producing command")
        if origin != cmd:
            if cmd["op"] != "deliver" or origin["op"] != "send":
                raise ValueError("event origin differs from dispatch without a scheduled delivery")
            sent = next((e for e in case["history"] if e["command_id"] == origin["command_id"]
                         and e["event_type"] == "TransferSent"), None)
            if sent is None or cmd["scheduled_work"]["command_id"] != f"communication:{sent['event_id']}":
                raise ValueError("delivery has no originating send parent")
        if not event["parents"] and event["event_type"] not in roots:
            raise ValueError("state change has no causal parent")
        if not event["parents"] and roots[event["event_type"]] != cmd["op"]:
            raise ValueError("state change cannot be reclassified as an external root")
        for parent in event["parents"]:
            if parent["event_id"] not in earlier:
                raise ValueError("missing or forward causal parent")
            if parent["relation"] not in {"direct_cause", "supporting_evidence", "association"}:
                raise ValueError("unknown causal parent relation")
        review.append({"event_id": event["event_id"], "event_type": event["event_type"],
                       "command_id": event["command_id"], "parents": event["parents"],
                       "dispatch_command_id": cmd["command_id"],
                       "external_root": not event["parents"]})
        earlier.add(event["event_id"])
    return review


def run_cases(seed, swap_kinds=False):
    return {name: replay_case(name, seed, plan, swap_kinds)
            for name, plan in strategies().items()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_gate(cases):
    closure, clarified = cases["closure"], cases["clarification"]
    lost, surviving = cases["sole_loss"], cases["surviving"]
    benign, wrong = cases["harmless"], cases["wrong_authority"]
    require(closure["metrics"]["closure_count"] == 1 and
            closure["metrics"]["evidence_backed_information_gain"] == 0, "closure/gain conflation")
    require(clarified["versions"][-1]["authority_basis"] == "delegated_discretion" and
            clarified["versions"][-1]["selected"] == "one" and
            clarified["metrics"]["evidence_backed_information_gain"] == 0, "clarification/authority failed")
    require(not lost["snapshots"][-1]["item_available"] and
            surviving["snapshots"][-1]["item_available"] and
            lost["versions"][-1]["selected"] == "three" and
            surviving["versions"][-1]["selected"] == "one", "holding-loss contrast failed")
    require(benign["versions"][-1]["support"] == "inconclusive" and
            benign["versions"][-1]["authority_basis"] == "inferred_without_authority",
            "benign counterexample erased")
    require(wrong["versions"][-1]["support"] == "challenged" and
            wrong["versions"][-1]["authority_basis"] == "policy_constraint" and
            wrong["snapshots"][-1]["rejected"] is not None, "wrong-authority counterexample erased")


def check_timing(seconds, budget):
    if not (math.isfinite(seconds) and math.isfinite(budget) and 0 <= seconds <= budget and budget > 0):
        raise ValueError("fresh timing exceeds or has invalid budget")


def parameter_manifest():
    definitions = [
        ("latency", "MA-04", 1, "tick", [1, 1], "toy_gameplay", "delayed arrival boundary", "longer delay"),
        ("capacity", "MA-04", 1, "message/tick", [1, 1], "toy_gameplay", "single message boundary", "buffered channel"),
        ("loss", "MA-04", 0, "probability", [0, 0], "toy_gameplay", "deterministic delivered control", "lossy route"),
        ("distortion", "MA-04", 0, "probability", [0, 0], "toy_gameplay", "preserve claim control", "distorted claim"),
        ("transfer_cost", "MA-04", 1, "resource unit/message", [1, 1], "toy_gameplay", "visible transfer cost", "other cost"),
        ("connection_cost", "MA-04", 0, "resource unit", [0, 0], "toy_gameplay", "minimal channel control", "paid connection"),
        ("trust", "MA-04", 0.5, "metadata ratio", [0.5, 0.5], "toy_gameplay", "unused default metadata", "explicit trust policy"),
        ("run_budget", "MA-14", BUDGET_SECONDS, "second", [30, 30], "engineering_budget", "bounded probe execution", "AE-033 measured budget"),
    ]
    return [{"parameter_id": name, "assumption_id": assumption, "value": value,
             "unit": unit, "range": bounds, "classification": classification,
             "rationale": rationale, "source": "invented for experiment", "calibration_version": None,
             "uncertainty": "boundary control only; no sensitivity or calibration evaluated" if assumption == "MA-04"
                            else "host load varies; no performance tuning claim",
             "alternatives": [alternative], "review_activity": "AE-018" if assumption == "MA-04" else "AE-033"}
            for name, assumption, value, unit, bounds, classification, rationale, alternative in definitions]


def artifacts():
    require(sys.version_info[:3] == (3, 12, 13), "CPython 3.12.13 required")
    start = time.perf_counter()
    boundary = check_dependency_boundary(ROOT / "src/agent_empires/simulation")
    runs = []
    for seed in SEEDS:
        cases = run_cases(seed)
        require(encode(cases) == encode(run_cases(seed)), f"repeat mismatch at seed {seed}")
        require(encode(cases) == encode(run_cases(seed, True)), f"actor label mismatch at seed {seed}")
        for name, case in cases.items():
            require(encode(case) == encode(replay_case(name, seed, case["commands"])),
                    f"recorded command replay mismatch at seed {seed}, case {name}")
        check_gate(cases)
        runs.append({"seed": seed, "cases": cases})
    paths = ["experiments/headless_probe.py", "tests/simulation/test_headless_probe.py",
             "research/experiments/AE-007/protocol.md", "pyproject.toml", "uv.lock"]
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "src/agent_empires/simulation").rglob("*.py"))]
    manifest = {"schema_version": 1, "model_version": MODEL_VERSION,
                "python": platform.python_version(), "dependencies": {"pytest": version("pytest")},
                "fixture_version": "ae007-three-holders-v1", "seeds": list(SEEDS), "rng_scheme": RNG_SCHEME,
                "initial_state": {"actors": ["worker:agent:team", "holder:human:team", "owner:human:team"],
                                  "holdings": [], "grants": [], "history": [], "tick": 0,
                                  "question": {"id": "choice", "topic": "retry_count", "scope": "work-item",
                                               "alternatives": list(OPTIONS)}, "profile": asdict(PROFILE)},
                "strategies": strategies(), "ordered_commands": "results.json runs[].cases[].commands",
                "parameters": parameter_manifest(),
                "budget_seconds": BUDGET_SECONDS,
                "controls": ["full-history repeat", "recorded-command replay", "all actor kinds swapped with profiles fixed",
                             "lost versus surviving holdings", "static simulation import boundary"],
                "input_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
                "classification": "structural toy-model gate; no architecture acceptance or empirical calibration"}
    seconds = time.perf_counter() - start
    check_timing(seconds, BUDGET_SECONDS)
    return {"results.json": {"schema_version": 1, "runs": runs, "boundary_checked": boundary,
                             "failed_controls": [], "failed_seeds": []},
            "run-manifest.json": manifest,
            "timing.json": {"seconds": seconds, "budget_seconds": BUDGET_SECONDS}}


def write_outputs(directory, outputs):
    directory.mkdir(parents=True, exist_ok=True)
    for name in OUTPUTS:
        if (directory / name).exists():
            raise FileExistsError(directory / name)
    for name, value in outputs.items():
        (directory / name).write_bytes(encode(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output-dir", type=Path)
    mode.add_argument("--verify-against", type=Path)
    args = parser.parse_args()
    if args.output_dir:
        # Refuse existing evidence before running any experiment.
        for name in OUTPUTS:
            if (args.output_dir / name).exists():
                raise FileExistsError(args.output_dir / name)
        outputs = artifacts()
        write_outputs(args.output_dir, outputs)
        print("PASS: three seeded runs, six cases each; repeat, relabeling, causal and boundary controls")
    else:
        expected = {name: json.loads((args.verify_against / name).read_bytes()) for name in OUTPUTS}
        require(expected["run-manifest.json"]["budget_seconds"] == BUDGET_SECONDS, "stale timing budget")
        with tempfile.TemporaryDirectory(prefix="ae007-verify-") as temporary:
            outputs = artifacts()
            write_outputs(Path(temporary), outputs)
            for name in ("results.json", "run-manifest.json"):
                actual = json.loads((Path(temporary) / name).read_bytes())
                require(encode(expected[name]) == encode(actual), f"stale evidence: {name}")
            check_timing(outputs["timing.json"]["seconds"], expected["run-manifest.json"]["budget_seconds"])
        print("PASS: canonical results and pinned manifest reproduced in temporary storage; fresh timing within budget; evidence unchanged")


if __name__ == "__main__":
    main()
