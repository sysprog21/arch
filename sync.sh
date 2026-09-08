#!/bin/sh
# Mirror pages from the CSIE wiki data repo into Jekyll pages.
set -eu

RAW=https://raw.githubusercontent.com/NCKUCSIE-Wiki/csiewiki-wikidata/refs/heads/main
WIKI=https://wiki.csie.ncku.edu.tw
INTRO='https://docs.google.com/presentation/d/1RwBZQDAgg0DRADH1lk06y4LEMcB1d_uYni_g2hK9mEA/edit?usp=sharing'

# mirror <wiki path> <output file> <permalink>
mirror() {
    curl -fsSL "$RAW/$1.page" |
    # The wiki closes its front matter with "..."; Jekyll insists on "---".
    awk -v wiki="/$1" -v link="$3" '
        NR > 1 && !done && /^\.\.\.$/ {
            print "layout: default"
            print "permalink: " link
            print "wiki: " wiki
            print "---"
            done = 1
            next
        }
        { print }' |
    sed \
        -e "s#\(\[Course Introduction\](\)[^)]*#\1$INTRO#" \
        -e 's#](/User/jserv)#]({{ site.baseurl }}/User/jserv)#g' \
        -e 's#](/arch/schedule)#]({{ site.baseurl }}/)#g' \
        -e "s#\](/#]($WIKI/#g" \
        -e 's#\$\\to\$#\&rarr;#g' \
        > "$2"
}

mkdir -p User
mirror arch/schedule index.md /
mirror User/jserv User/jserv.md /User/jserv/
