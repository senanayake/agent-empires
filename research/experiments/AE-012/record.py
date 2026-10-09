"""Save actual command output, exit status and timing for worker evidence."""
import json
from pathlib import Path
import subprocess
import sys
import time

path, *command = sys.argv[1:]
started = time.perf_counter()
try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    receipt = dict(command=' '.join(command), exit_code=result.returncode,
                   stdout=result.stdout, stderr=result.stderr, status='passed' if result.returncode == 0 else 'failed')
except subprocess.TimeoutExpired as error:
    receipt = dict(command=' '.join(command), exit_code=None, stdout=str(error.stdout), stderr=str(error.stderr), status='timed_out')
receipt['elapsed_seconds'] = time.perf_counter() - started
Path(path).write_text(json.dumps(receipt, indent=2) + '\n')
print(f"{receipt['status']}: {receipt['command']} ({receipt['elapsed_seconds']:.3f}s)")
print(receipt['stdout'][-2000:])
print(receipt['stderr'][-1000:])
sys.exit(receipt['exit_code'] if receipt['exit_code'] is not None else 124)
