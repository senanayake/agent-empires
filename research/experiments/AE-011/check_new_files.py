"""Supplement tracked diff-check with Git's whitespace check on new files."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
paths = [root / 'experiments/trace_report.py', root / 'tests/unit/test_trace_report.py',
         root / 'docs/campaigns/mvp/evidence/AE-011.json']
paths += [p for p in (root / 'research/experiments/AE-011').rglob('*')
          if p.is_file() and '__pycache__' not in p.parts]
for path in sorted(paths):
    command = ['git', 'diff', '--no-index', '--check', '/dev/null', str(path.relative_to(root))]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if result.returncode not in (0, 1) or result.stdout or result.stderr:
        print(command, result.returncode, result.stdout, result.stderr)
        raise SystemExit(1)
print(f'PASS: Git whitespace check for {len(paths)} current activity files; no diagnostics')
