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
    gh.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\n'
                  'cat "$FIXTURE"\nexit "${API_STATUS:-0}"\n')
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
             for owner in ['zebra', 'Alice']]
    fixture.write_text(json.dumps([[forks[0]], [forks[1]]]))

    def run(*args):
        return subprocess.run([str(repo / 'homework1.sh'), *args],
                              cwd=root, env=env, capture_output=True, text=True)

    result = run('--update-only')
    assert result.returncode == 0, result.stderr
    datafile = repo / '_data/homework1.json'
    data = json.loads(datafile.read_text())
    assert [f['owner'] for f in data['forks']] == ['Alice', 'zebra']
    assert '--paginate --slurp' in calls.read_text()
    assert 'per_page=100&sort=oldest' in calls.read_text()
    assert 'push origin main' not in calls.read_text()
    original = datafile.read_text()
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
