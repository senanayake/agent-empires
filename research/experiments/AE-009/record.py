"""Capture actual command output without substituting a different runtime."""
import json
from pathlib import Path
import subprocess
import sys

name, *command = sys.argv[1:]
result = subprocess.run(command, text=True, capture_output=True, timeout=300)
record = dict(command=command, exit_code=result.returncode,
              stdout=result.stdout, stderr=result.stderr)
Path(__file__).with_name(name + '.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
sys.exit(result.returncode)
