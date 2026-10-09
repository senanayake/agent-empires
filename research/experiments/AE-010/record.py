"""Capture actual commands under the checkout-local selected runtime."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
name, command = sys.argv[1:]
env = dict(os.environ, PATH=str(ROOT / '.venv/bin') + os.pathsep + os.environ['PATH'])
start = time.perf_counter()
result = subprocess.run(command, shell=True, cwd=ROOT, env=env, capture_output=True, text=True)
receipt = dict(command=command, exit_code=result.returncode, stdout=result.stdout,
               stderr=result.stderr, elapsed_seconds=time.perf_counter() - start)
(ROOT / 'research/experiments/AE-010' / (name + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
sys.exit(result.returncode)
