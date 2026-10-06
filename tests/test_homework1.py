"""Run with python3 tests/test_homework1.py (requires jq, no network)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    repo = root / 'repo'
    repo.mkdir()
    shutil.copy2(Path(__file__).resolve().parents[1] / 'homework1.sh', repo)
    gh = root / 'gh'
    gh.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['CALLS'], 'a') as calls:
    calls.write(' '.join(sys.argv[1:]) + '\\n')
endpoint = next(arg for arg in sys.argv if arg.startswith('repos/'))
if '/forks?' in endpoint:
    print(open(os.environ['FIXTURE']).read())
    sys.exit(int(os.environ.get('API_STATUS', '0')))
if '/branches?' in endpoint and os.environ.get('BRANCH_STATUS') == '1':
    sys.exit(1)
if '/compare/' in endpoint and os.environ.get('COMPARE_STATUS') == '1':
    sys.exit(1)
if endpoint.endswith('/commits/main'):
    print(json.dumps({'sha': 'upstream'}))
elif '/branches?' in endpoint:
    owner = endpoint.split('/')[1]
    sha = {'zebra': 'ahead', 'behind': 'behind', 'diverged': 'diverged'}.get(owner, 'upstream')
    # Alice has an unchanged main but an updated branch on the second page.
    print(json.dumps([[{'name': 'main', 'commit': {'sha': sha}}],
                      [{'name': 'feature/test', 'commit': {'sha': 'ahead' if owner == 'Alice' else sha}}]]))
else:
    sha = endpoint.split('...')[1].split('?')[0]
    print(json.dumps({'ahead_by': {'ahead': 1, 'behind': 0, 'diverged': 2}[sha]}))
''')
    gh.chmod(0o755)
    git = root / 'git'
    git.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\n'
                   'if [ "$1" = branch ]; then echo main; fi\n')
    git.chmod(0o755)
    fixture = root / 'forks.json'
    calls = root / 'calls'
    env = dict(os.environ, PATH=f'{root}:{os.environ["PATH"]}',
               FIXTURE=str(fixture), CALLS=str(calls))
    forks = [dict(owner=dict(login=owner), full_name=f'{owner}/minirubik',
                  html_url=f'https://github.com/{owner}/minirubik', pushed_at=None)
             for owner in ['zebra', 'Alice', 'behind', 'diverged', 'same']]
    fixture.write_text(json.dumps([forks[:1], forks[1:]]))

    def run(*args):
        return subprocess.run([str(repo / 'homework1.sh'), *args],
                              cwd=root, env=env, capture_output=True, text=True)

    result = run('--update-only')
    assert result.returncode == 0, result.stderr
    datafile = repo / '_data/homework1.json'
    data = json.loads(datafile.read_text())
    assert [f['owner'] for f in data['forks']] == ['Alice', 'behind', 'diverged', 'same', 'zebra']
    assert {f['owner']: f['has_updates'] for f in data['forks']} == {
        'Alice': True, 'behind': False, 'diverged': True, 'same': False, 'zebra': True}
    assert data['upstream_sha'] == 'upstream'
    assert calls.read_text().count('/compare/upstream...ahead') == 1
    comparisons = [line for line in calls.read_text().splitlines() if '/compare/' in line]
    assert len(comparisons) == 3  # Shared SHAs are compared once, even across workers.
    assert all('?per_page=1' in line for line in comparisons)
    assert calls.read_text().count('/branches?per_page=100') == len(forks)
    assert '--paginate --slurp' in calls.read_text()
    assert 'per_page=100&sort=oldest' in calls.read_text()
    assert 'push origin main' not in calls.read_text()
    original = datafile.read_text()
    for failure in ['BRANCH_STATUS', 'COMPARE_STATUS']:
        env[failure] = '1'
        assert run('--update-only').returncode != 0
        assert datafile.read_text() == original
        assert not list(datafile.parent.glob('homework1.json.*'))
        assert 'push origin main' not in calls.read_text()
        del env[failure]
    for content, status in [('[]', '22'), ('{}', '0'),
                            ('[[{"owner":{"login":"x"}}]]', '0')]:
        fixture.write_text(content)
        env['API_STATUS'] = status
        assert run('--update-only').returncode != 0
        assert datafile.read_text() == original
        assert not list(datafile.parent.glob('homework1.json.*'))
    env['API_STATUS'] = '0'
    fixture.write_text('[[]]')
    assert run().returncode == 0
    assert json.loads(datafile.read_text())['forks'] == []
    assert 'push origin main' in calls.read_text()
print('homework1 update/publish checks passed')
