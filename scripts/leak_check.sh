#!/bin/sh
# Leak check (Sprint 7 M6): run before pushing to the public repo.
#
#   scripts/leak_check.sh [ref [base]]     # default HEAD, origin/main
#
# Scans the tree at <ref> (tracked content only, never the working folder)
# for the dev's global git email, home folder and user name, token shapes, and
# backlog files that must never be published. Also checks the author and
# committer emails of every commit in <ref> that <base> doesn't have.
# Nothing personal is written here: the patterns come from this machine at
# run time, so the script itself is safe to publish.

ref=${1:-HEAD}
base=${2:-origin/main}
self=scripts/leak_check.sh
found=0

hit() {
    echo "$1"
    found=1
}

git rev-parse --verify --quiet "$ref^{commit}" >/dev/null || {
    echo "leak check: unknown ref $ref" >&2
    exit 2
}

# Content: one fixed string at a time, so nothing in a pattern is a regex.
email=$(git config --global user.email)
user=$(whoami)
for pattern in "$email" "$HOME" "/Users/$user" "/home/$user"; do
    [ -n "$pattern" ] || continue
    matches=$(git grep -n -I -F -e "$pattern" "$ref" -- ":!$self")
    [ -n "$matches" ] && hit "$matches"
done

# Token shapes.
matches=$(git grep -n -I -E \
    -e 'gh[po]_[A-Za-z0-9]{20,}' \
    -e 'github_pat_[A-Za-z0-9_]{20,}' \
    -e 'sk-[A-Za-z0-9_-]{20,}' \
    -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
    "$ref" -- ":!$self")
[ -n "$matches" ] && hit "$matches"

# Files that are local-only by design.
files=$(git ls-tree -r --name-only "$ref" | grep -E \
    -e '(^|/)guidelines/(backlog|motivation)\.md$' \
    -e '^postponedfeatures\.md$' \
    -e '^bug-report-[^/]*$')
[ -n "$files" ] && hit "local-only file in tree: $files"

# Identities on the commits that would be pushed.
if [ -n "$email" ] && git rev-parse --verify --quiet "$base" >/dev/null; then
    commits=$(git log --format='%h %ae %ce' "$base..$ref" | grep -F -e "$email")
    [ -n "$commits" ] && hit "commit identity: $commits"
fi

if [ "$found" -ne 0 ]; then
    echo "leak check: FAILED" >&2
    exit 1
fi
echo "leak check: clean"
