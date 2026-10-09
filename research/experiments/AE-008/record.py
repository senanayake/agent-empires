"""Run bounded local checks and retain their real output; no evidence fabrication."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

name, timeout, *command = sys.argv[1:]
root = Path(__file__).resolve().parents[3]
env = os.environ.copy()
env['PATH'] = str(root / '.venv/bin') + os.pathsep + env['PATH']
start = time.monotonic()
try:
    run = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                         timeout=int(timeout))
    result = dict(command=' '.join(command), exit_code=run.returncode,
                  stdout=run.stdout, stderr=run.stderr, timed_out=False)
except subprocess.TimeoutExpired as exc:
    result = dict(command=' '.join(command), exit_code=None,
                  stdout=(exc.stdout or b'').decode(), stderr=(exc.stderr or b'').decode(), timed_out=True)
result['elapsed_seconds'] = time.monotonic() - start
(root / 'research/experiments/AE-008' / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(result['stdout'][-4000:])
print(result['stderr'][-1000:])
sys.exit(result['exit_code'] if result['exit_code'] is not None else 124)
