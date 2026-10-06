#!/usr/bin/env bash
# Refresh every minirubik fork and publish through the existing Pages workflow.
# Requires authenticated gh, jq, python3, and git. --update-only skips publishing.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ $# -gt 1 || (${1:-} != '' && ${1:-} != --update-only) ]]; then
    echo "Usage: $0 [--update-only]" >&2
    exit 1
fi
if [[ ${1:-} != --update-only ]]; then
    [[ $(git branch --show-current) == main ]] || { echo 'Publish from main.' >&2; exit 1; }
    [[ -z $(git status --porcelain) ]] || { echo 'Commit or stash local changes before publishing.' >&2; exit 1; }
    git fetch origin main
    git merge --ff-only origin/main
fi

mkdir -p _data
tmp=$(mktemp _data/homework1.json.XXXXXX)
trap 'rm -f "$tmp"' EXIT
gh api --hostname github.com --paginate --slurp \
    'repos/sysprog21/minirubik/forks?per_page=100&sort=oldest' |
    jq -e --arg updated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
        if type == "array" and all(.[]; type == "array") then .
        else error("Invalid paginated response") end |
        [.[][] | {owner: .owner.login, repository: .full_name,
                  url: .html_url, pushed_at: .pushed_at}] |
        if all(.[]; . as $fork | (.owner | type == "string") and
                    (.repository | type == "string") and
                    (.url == "https://github.com/" + .repository) and
                    (.repository | startswith($fork.owner + "/"))) then
            {updated_at: $updated_at, forks: sort_by(.owner | ascii_downcase)}
        else error("Invalid fork metadata") end' > "$tmp"
python3 - "$tmp" <<'PY'
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

def api(endpoint, paginate=False):
    args = ['gh', 'api', '--hostname', 'github.com', endpoint]
    if paginate:
        args += ['--paginate', '--slurp']
    return json.loads(subprocess.check_output(args, text=True))

path = Path(sys.argv[1])
data = json.loads(path.read_text())
base = api('repos/sysprog21/minirubik/commits/main')['sha']
data['upstream_sha'] = base
def branch_shas(fork):
    pages = api(f"repos/{fork['repository']}/branches?per_page=100", paginate=True)
    return {branch['commit']['sha'] for page in pages for branch in page}

def has_updates(sha):
    comparison = api(f'repos/sysprog21/minirubik/compare/{base}...{sha}?per_page=1')
    return comparison['ahead_by'] > 0

with ThreadPoolExecutor(max_workers=8) as pool:
    branches = list(pool.map(branch_shas, data['forks']))
    unique_shas = sorted(set().union(*branches) - {base})
    print(f'Checked {len(branches)} forks; comparing {len(unique_shas)} unique commits',
          file=sys.stderr)
    ahead = dict(zip(unique_shas, pool.map(has_updates, unique_shas)))
ahead[base] = False
for fork, shas in zip(data['forks'], branches):
    fork['has_updates'] = any(ahead[sha] for sha in shas)
path.write_text(json.dumps(data, indent=2) + '\n')
PY
chmod 644 "$tmp"
mv "$tmp" _data/homework1.json

if [[ ${1:-} != --update-only ]]; then
    git add -- _data/homework1.json
    git commit -m 'Update homework 1 fork list'
    git push origin main
    echo 'Pages deployment triggered: https://sysprog21.github.io/arch/homework1.html'
fi
