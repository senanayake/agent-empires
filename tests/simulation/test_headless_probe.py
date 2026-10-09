import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "experiments/headless_probe.py"
spec = importlib.util.spec_from_file_location("headless_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.parametrize("seed", [7, 19, 31])
def test_complete_histories_repeat_and_actor_kind_has_no_effect(seed):
    baseline = probe.run_cases(seed)
    assert probe.encode(baseline) == probe.encode(probe.run_cases(seed))
    assert probe.encode(baseline) == probe.encode(probe.run_cases(seed, swap_kinds=True))
    for case in baseline.values():
        assert len(case["commands"]) == len(case["snapshots"])
        probe.review_causality(case)
    for name, case in baseline.items():
        assert probe.encode(case) == probe.encode(probe.replay_case(name, seed, case["commands"]))


def test_closure_authority_and_evidence_remain_independent():
    cases = probe.run_cases(7)
    closure = cases["closure"]
    assert closure["versions"][-1]["authority_basis"] == "inferred_without_authority"
    assert closure["metrics"]["closure_count"] == 1
    assert closure["metrics"]["evidence_backed_information_gain"] == 0
    assert closure["versions"][-1]["confidence"] == "high"
    clarified = cases["clarification"]
    send = next(s for s in clarified["snapshots"] if s["op"] == "send")
    assert send["worker_holdings"] == []
    delivered = next(s for s in clarified["snapshots"] if s["op"] == "deliver")
    assert len(delivered["worker_holdings"]) == 1
    assert clarified["versions"][-1]["authority_basis"] == "delegated_discretion"
    # Clarification of an organizational choice need not be world evidence.
    assert clarified["metrics"]["evidence_backed_information_gain"] == 0
    assert clarified["versions"][-1]["selected"] == "one"


def test_departure_moves_loss_only_when_no_holding_survives():
    cases = probe.run_cases(19)
    lost, survived = cases["sole_loss"], cases["surviving"]
    assert not lost["snapshots"][-1]["item_available"]
    assert survived["snapshots"][-1]["item_available"]
    assert lost["versions"][-1]["selected"] == "three"
    assert survived["versions"][-1]["selected"] == "one"
    assert any(e["event_type"] == "KnowledgeLost" for e in lost["history"])
    assert not any(e["event_type"] == "KnowledgeLost" for e in survived["history"])
    assert survived["metrics"]["evidence_backed_information_gain"] == 0
    selected = next(e for e in survived["history"] if e["event_type"] == "DecisionSelected")
    parents = {p["event_id"] for p in selected["parents"]}
    transfer = next(e for e in survived["history"] if e["event_type"] == "KnowledgeTransferred")
    assert transfer["event_id"] in parents


def test_benign_and_challenged_authority_are_preserved_without_truth_score():
    cases = probe.run_cases(31)
    benign, wrong = cases["harmless"], cases["wrong_authority"]
    assert benign["versions"][-1]["authority_basis"] == "inferred_without_authority"
    assert benign["versions"][-1]["support"] == "inconclusive"
    assert wrong["versions"][-1]["authority_basis"] == "policy_constraint"
    assert wrong["versions"][-1]["support"] == "challenged"
    assert wrong["versions"][0]["support"] == "none"
    assert wrong["metrics"]["evidence_backed_information_gain"] == 1
    assert "correct" not in wrong["versions"][-1]
    assert any(s.get("rejected") for s in wrong["snapshots"])
    assert not any(e["event_type"] == "IncidentOccurred" for e in benign["history"])


def test_causal_review_rejects_missing_or_forward_parent():
    case = probe.run_cases(7)["surviving"]
    event = next(e for e in case["history"] if e["event_type"] == "KnowledgeTransferred")
    event["parents"] = [{"event_id": "not-an-earlier-event", "relation": "direct_cause"}]
    with pytest.raises(ValueError, match="parent"):
        probe.review_causality(case)


def test_scheduled_delivery_keeps_origin_and_dispatch_distinct():
    case = probe.run_cases(7)["clarification"]
    sent = next(c for c in case["commands"] if c["op"] == "send")
    delivered = next(c for c in case["commands"] if c["op"] == "deliver")
    facts = [r for r in case["causal_review"] if r["dispatch_command_id"] == delivered["command_id"]]
    assert facts and all(r["command_id"] == sent["command_id"] for r in facts)
    delivered["scheduled_work"]["command_id"] = "wrong-send"
    with pytest.raises(ValueError, match="send parent"):
        probe.review_causality(case)


def test_state_change_without_causal_parent_is_rejected():
    case = probe.run_cases(7)["surviving"]
    event = next(e for e in case["history"] if e["event_type"] == "KnowledgeTransferred")
    event["parents"] = []
    with pytest.raises(ValueError, match="causal parent"):
        probe.review_causality(case)


def test_received_holding_cannot_be_reclassified_as_external_setup():
    case = probe.run_cases(7)["surviving"]
    event = next(e for e in case["history"] if e["event_type"] == "KnowledgeHoldingRecorded"
                 and e["parents"])
    event["parents"] = []
    with pytest.raises(ValueError, match="external root"):
        probe.review_causality(case)


@pytest.mark.parametrize("code", [
    "import requests", "from agent_empires.application import commands",
    "from ..adapters import http", "import godot", "import urllib.request",
    "import importlib; importlib.import_module('requests')",
])
def test_dependency_boundary_detects_forbidden_imports(tmp_path, code):
    (tmp_path / "bad.py").write_text(code)
    with pytest.raises(ValueError, match="import"):
        probe.check_dependency_boundary(tmp_path)


def test_actual_simulation_dependency_boundary():
    assert probe.check_dependency_boundary(ROOT / "src/agent_empires/simulation")


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)


def test_cli_replay_detects_tampering_and_never_overwrites(tmp_path):
    assert cli("--output-dir", tmp_path).returncode == 0
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert cli("--verify-against", tmp_path).returncode == 0
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert cli("--output-dir", tmp_path).returncode != 0
    manifest_path = tmp_path / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["budget_seconds"] = 0
    manifest_path.write_text(json.dumps(manifest))
    bad_budget = manifest_path.read_bytes()
    rejected = cli("--verify-against", tmp_path)
    assert rejected.returncode != 0 and "budget" in rejected.stderr
    assert manifest_path.read_bytes() == bad_budget
    manifest_path.write_bytes(before["run-manifest.json"])
    data = json.loads((tmp_path / "results.json").read_text())
    data["runs"][0]["cases"]["closure"]["metrics"]["closure_count"] = 999
    (tmp_path / "results.json").write_text(json.dumps(data))
    tampered = (tmp_path / "results.json").read_bytes()
    assert cli("--verify-against", tmp_path).returncode != 0
    assert (tmp_path / "results.json").read_bytes() == tampered


def test_output_refuses_partial_evidence_and_verify_enforces_budget(tmp_path):
    (tmp_path / "timing.json").write_text("existing evidence")
    assert cli("--output-dir", tmp_path).returncode != 0
    assert not (tmp_path / "results.json").exists()
    with pytest.raises(ValueError, match="budget"):
        probe.check_timing(31, 30)
    with pytest.raises(ValueError, match="budget"):
        probe.check_timing(0, 0)
