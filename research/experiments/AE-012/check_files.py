"""Check scoped files, import direction, syntax and new-file whitespace."""
import ast
from pathlib import Path
import subprocess

files = [Path('src/agent_empires/simulation/learning.py'), Path('experiments/clarification_comparison.py'),
         Path('tests/simulation/test_clarification.py'), Path('docs/model-assumptions.md')]
files += [p for p in Path('research/experiments/AE-012').rglob('*') if p.is_file() and p.suffix != '.gz']
for path in files:
    data = path.read_bytes()
    assert data.endswith(b'\n'), path
    assert not any(line.rstrip() != line for line in data.decode().splitlines()), path
    if path.suffix == '.py':
        ast.parse(data)
owner = ast.parse(Path('src/agent_empires/simulation/learning.py').read_text())
for node in ast.walk(owner):
    if isinstance(node, ast.ImportFrom):
        assert node.level == 1 or node.module in ('dataclasses',), node.module
    if isinstance(node, ast.Import):
        raise AssertionError('Unexpected absolute simulation dependency')
allowed = ('src/agent_empires/simulation/learning.py', 'experiments/clarification_comparison.py',
           'tests/simulation/test_clarification.py', 'research/experiments/AE-012/',
           'docs/campaigns/mvp/evidence/AE-012.json', 'docs/model-assumptions.md')
changed = subprocess.check_output(['git', 'ls-files', '--modified', '--others', '--exclude-standard'], text=True)
assert all(any(path == a or (a.endswith('/') and path.startswith(a)) for a in allowed)
           for path in changed.splitlines()), changed
print('PASS: scoped files, Python syntax, simulation import boundary and new-file whitespace')
