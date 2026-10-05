#!/usr/bin/env bash
# Refresh every minirubik fork and publish through the existing Pages workflow.
# Requires authenticated gh, jq, and git. --update-only skips committing/publishing.
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
chmod 644 "$tmp"
mv "$tmp" _data/homework1.json

if [[ ${1:-} != --update-only ]]; then
    git add -- _data/homework1.json
    git commit -m 'Update homework 1 fork list'
    git push origin main
    echo 'Pages deployment triggered: https://sysprog21.github.io/arch/homework1.html'
fi
