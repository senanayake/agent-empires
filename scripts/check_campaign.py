#!/usr/bin/env python3
"""Check planning consistency and evidence references; never judge scientific truth."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


FIELDS = (
    "Objective", "Why now", "Deliverables", "Dependencies", "Acceptance criteria",
    "Tests", "Risks / questions", "Explicit non-goals", "Estimated complexity",
)
MANIFEST = Path("docs/campaigns/mvp/campaign.json")
DOCUMENT = Path("docs/mvp-campaign.md")
HUMAN_MINIMUMS = {"AE-029": 5}
OWNER_DIRECTION_GATES = {"AE-011", "AE-019"}
OWNER_REVISION = "docs/campaigns/mvp/revisions/2026-10-09-owner-feedback.md"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_activities(markdown):
    activities = {}
    pattern = r"^### (AE-\d{3}) — ([^\n]+)\n(.*?)(?=^### AE-|^## 11\.|\Z)"
    for match in re.finditer(pattern, markdown, re.MULTILINE | re.DOTALL):
        activity_id, title, body = match.groups()
        require(activity_id not in activities, f"Duplicate document ID: {activity_id}")
        fields = dict(re.findall(r"^- \*\*(.+?):\*\* (.+)$", body, re.MULTILINE))
        require(set(fields) == set(FIELDS), f"{activity_id}: missing/extra activity fields")
        require(all(value.strip() for value in fields.values()), f"{activity_id}: blank field")
        size = fields["Estimated complexity"].rstrip(".")
        require(size in {"XS", "S", "M", "L", "XL"}, f"{activity_id}: invalid size")
        activities[activity_id] = {"title": title, **fields}
    require(activities, "No activity sections found")
    return activities


def check_plan(root):
    markdown = (root / DOCUMENT).read_text()
    activities = parse_activities(markdown)
    manifest = json.loads((root / MANIFEST).read_text())
    queues = manifest["queues"]
    ids = [queue["id"] for queue in queues]
    require(len(ids) == len(set(ids)), "Duplicate manifest queue ID")
    require(set(ids) == set(activities), "Manifest/document activity IDs differ")
    require(manifest.get("active_queue") in ids, "Unknown active queue")
    sections = re.findall(r"^## (\d+)\. ", markdown, re.MULTILINE)
    require(sections == [str(i) for i in range(1, 16)], "Expected campaign sections 1–15")
    graph = {}
    for queue in queues:
        activity_id = queue["id"]
        fields = activities[activity_id]
        require(queue["title"] == fields["title"], f"{activity_id}: title drift")
        require(queue["goal"] == fields["Objective"], f"{activity_id}: objective drift")
        for field in ("Why now", "Deliverables", "Risks / questions", "Explicit non-goals", "Estimated complexity"):
            require(f"{field}: {fields[field]}" in queue["scope"], f"{activity_id}: {field} drift")
        require(fields["Acceptance criteria"] in queue["done_when"], f"{activity_id}: acceptance drift")
        require(f"Tests: {fields['Tests']}" in queue["scope"], f"{activity_id}: test-plan drift")
        expected = re.findall(r"AE-\d{3}", fields["Dependencies"])
        dependencies = queue.get("depends_on", [])
        require(dependencies == expected, f"{activity_id}: dependency drift")
        require(all(dep in ids and dep != activity_id for dep in dependencies), f"{activity_id}: invalid dependency")
        require(len(dependencies) == len(set(dependencies)), f"{activity_id}: duplicate dependency")
        require(queue.get("allowed_paths"), f"{activity_id}: missing allowed paths")
        require(queue.get("stop_if"), f"{activity_id}: missing stop rules")
        checks = queue.get("validation", [])
        receipt_command = f"python3 scripts/check_campaign.py --activity {activity_id}"
        require(any(c["command"] == receipt_command and c.get("required", True) for c in checks), f"{activity_id}: missing required receipt check")
        require(all(c.get("command") and c.get("name") for c in checks), f"{activity_id}: empty validation")
        graph[activity_id] = dependencies

    visited, active = set(), set()

    def visit(node):
        require(node not in active, f"Dependency cycle at {node}")
        if node in visited:
            return
        active.add(node)
        for dependency in graph[node]:
            visit(dependency)
        active.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return manifest, activities


def checked_file(root, relative):
    require(isinstance(relative, str) and relative.strip(), "Evidence path must be nonempty")
    require(not Path(relative).is_absolute(), f"Evidence path must be repository-relative: {relative}")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"Evidence path escapes repository: {relative}")
    require(path.is_file(), f"Missing evidence/input: {relative}")
    return path


def check_hash(root, relative, expected):
    path = checked_file(root, relative)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == expected, f"Evidence/input hash mismatch: {relative}")


def check_receipt(root, activity_id):
    relative = f"docs/campaigns/mvp/evidence/{activity_id}.json"
    receipt = json.loads(checked_file(root, relative).read_text())
    require(receipt.get("schema_version") == 1, "Unsupported receipt schema")
    require(receipt.get("activity_id") == activity_id, "Receipt activity ID mismatch")
    require(receipt.get("outcome") == "pass", f"{activity_id}: gate is not pass; revise before advancing")
    for field in ("summary", "reviewer", "review_notes"):
        require(isinstance(receipt.get(field), str) and receipt[field].strip(), f"Receipt needs {field}")
    require(isinstance(receipt.get("limitations"), list), "Receipt needs explicit limitations list")
    inputs = receipt.get("inputs")
    require(isinstance(inputs, dict) and inputs, "Receipt must bind relevant input files")
    for relative_input, digest in inputs.items():
        check_hash(root, relative_input, digest)
    artifacts = receipt.get("artifacts")
    require(isinstance(artifacts, list) and artifacts, "Receipt must cite evidence artifacts")
    for artifact in artifacts:
        require(isinstance(artifact, dict), "Evidence artifact must be an object")
        require(artifact.get("kind") in {"test_result", "experiment_result", "domain_review", "human_study", "manual_check"}, "Unknown evidence kind")
        check_hash(root, artifact["path"], artifact["sha256"])
    if activity_id in OWNER_DIRECTION_GATES:
        require(receipt.get("scope_revision") == OWNER_REVISION,
                "Early engineering gate needs the approved scope revision")
        require(OWNER_REVISION in inputs and
                any(a["path"] == OWNER_REVISION and a["kind"] == "domain_review" for a in artifacts),
                "Early engineering gate must bind its scope revision")
        require(receipt.get("acceptance_basis") == "engineering_and_owner_direction",
                "Early gate accepts engineering and owner direction only")
        require(receipt.get("human_validation") == "deferred_to_AE-029",
                "Early gate must retain deferred player validation")
    if activity_id in HUMAN_MINIMUMS:
        participants = receipt.get("participants", [])
        require(isinstance(participants, list) and all(isinstance(p, str) and p.strip() for p in participants), "Expected anonymized participant IDs")
        require(len(set(participants)) >= HUMAN_MINIMUMS[activity_id], "Missing required actual participant records")
        require(any(a["kind"] == "human_study" for a in artifacts), "Missing human-study evidence reference")
    if activity_id == "AE-030":
        require(any(a["kind"] == "human_study" for a in artifacts), "Hardening gate needs current or retested human-study evidence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--activity", help="Also require this activity's passing evidence receipt")
    args = parser.parse_args()
    try:
        _, activities = check_plan(args.root)
        if args.activity:
            require(args.activity in activities, "Unknown activity ID")
            check_receipt(args.root, args.activity)
        print(f"PASS: {len(activities)} activities; document/manifest fields and dependency DAG agree")
        if args.activity:
            print(f"PASS: {args.activity} receipt references/hashes; substantive acceptance still needs review")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
