"""Record exact combined command output as JSON, with a bounded timeout."""
import argparse
import json
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('output', type=Path)
p.add_argument('--timeout', type=float, default=120)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
start = time.monotonic()
try:
    r = subprocess.run(a.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, timeout=a.timeout)
    result = dict(command=a.command, exit_code=r.returncode, output=r.stdout,
                  status='passed' if r.returncode == 0 else 'failed')
except subprocess.TimeoutExpired as e:
    result = dict(command=a.command, exit_code=None, output=(e.stdout or b'').decode(), status='timed_out')
result['elapsed_seconds'] = time.monotonic() - start
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
