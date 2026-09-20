#!/usr/bin/env bash
# Mirror pages from the CSIE wiki data repo into Jekyll pages.
set -euo pipefail

RAW=https://raw.githubusercontent.com/NCKUCSIE-Wiki/csiewiki-wikidata/refs/heads/main
WIKI=https://wiki.csie.ncku.edu.tw
INTRO='https://docs.google.com/presentation/d/1RwBZQDAgg0DRADH1lk06y4LEMcB1d_uYni_g2hK9mEA/edit?usp=sharing'

# mirror <wiki path> <output file> <permalink>
mirror() {
    local tmp
    tmp=$(mktemp "$2.XXXXXX")
    trap 'rm -f "$tmp"' EXIT

    curl -fsSL "$RAW/$1.page" |
    # The wiki closes its front matter with "..."; Jekyll insists on "---".
    awk -v source="$1.page" -v wiki="/$1" -v link="$3" '
        NR > 1 && !done && /^\.\.\.$/ {
            print "layout: default"
            print "permalink: " link
            print "wiki: " wiki
            print "---"
            done = 1
            next
        }
        { print }
        END {
            if (!done) {
                print source ": missing YAML front-matter terminator" > "/dev/stderr"
                exit 1
            }
        }' |
    sed \
        -e "s#\(\[Course Introduction\](\)[^)]*#\1$INTRO#" \
        -e 's#](/User/jserv)#]({{ site.baseurl }}/User/jserv)#g' \
        -e 's#](/arch/schedule)#]({{ site.baseurl }}/)#g' \
        -e "s#\](/#]($WIKI/#g" \
        -e 's#\$\\to\$#\&rarr;#g' \
        > "$tmp"

    chmod 644 "$tmp"
    mv "$tmp" "$2"
    trap - EXIT
}

mkdir -p User
mirror arch/schedule index.md /
mirror User/jserv User/jserv.md /User/jserv/
