"""Record actual commands/results once; preserve failed checks as raw evidence."""
import json
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    destination = Path(__file__).resolve().parent / sys.argv[1]
    command = sys.argv[2:]
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    with destination.open('x') as output:
        json.dump(dict(command=' '.join(command), exit_code=result.returncode,
                       stdout=result.stdout, stderr=result.stderr), output, indent=2)
        output.write('\n')
    print(result.stdout, result.stderr, sep='', end='')
    raise SystemExit(result.returncode)
