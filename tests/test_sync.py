"""Run with python3 tests/test_sync.py; no network access needed."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    repo = root / "repo"
    repo.mkdir()
    shutil.copy2(Path(__file__).resolve().parents[1] / "sync.sh", repo)
    curl = root / "curl"
    curl.write_text('#!/bin/sh\ncat "$SYNC_FIXTURE"\nexit "${SYNC_STATUS:-0}"\n')
    curl.chmod(0o755)
    fixture = root / "source.page"
    env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
               SYNC_FIXTURE=str(fixture))

    def run():
        return subprocess.run([str(repo / "sync.sh")], cwd=root, env=env,
                              capture_output=True, text=True)

    fixture.write_text('---\ntitle: Test\n...\n'
                       '[Instructor](/User/jserv) [Schedule](/arch/schedule) '
                       '[Wiki](/other) $\\to$\n'
                       '[Course Introduction](https://example.com)\n')
    result = run()
    assert result.returncode == 0, result.stderr
    page = (repo / "index.md").read_text()
    assert 'layout: default\npermalink: /\nwiki: /arch/schedule\n---' in page
    assert '[Instructor]({{ site.baseurl }}/User/jserv)' in page
    assert '[Schedule]({{ site.baseurl }}/)' in page
    assert '[Wiki](https://wiki.csie.ncku.edu.tw/other) &rarr;' in page
    assert '[Course Introduction](https://docs.google.com/presentation/' in page
    assert 'permalink: /User/jserv/' in (repo / 'User/jserv.md').read_text()
    assert not (root / 'index.md').exists()

    for content, status in [('not YAML\n...\n', '0'),
                            ('---\ntitle: Missing terminator\n', '0'),
                            ('---\ntitle: Partial download\n...\n', '22')]:
        fixture.write_text(content)
        env['SYNC_STATUS'] = status
        assert run().returncode != 0
        assert (repo / 'index.md').read_text() == page
        assert not list(repo.glob('index.md.*'))

print('sync checks passed')
