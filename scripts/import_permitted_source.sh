#!/usr/bin/env bash
# One-time source-only import from the author's publicly visible, permitted repo.
# Never push APKs, game data, artwork, audio, private state, or credentials.
set -Eeuo pipefail

TARGET="HmoobGod/FFBE-Custom"
UPSTREAM_URL="https://github.com/Elvlin/exvius-offline.git"
UPSTREAM_SHA="b520e563cbc4364a07ee40331012340dc8aeb841"
WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"
TMPROOT="${RUNNER_TEMP:-$(mktemp -d)}"
SRC="$TMPROOT/ffbe-upstream-source-only"

if [[ "${GITHUB_REPOSITORY:-$TARGET}" != "$TARGET" ]]; then
  echo "Refusing to operate on a different repository" >&2
  exit 1
fi
if [[ "$(git -C "$WORKSPACE" remote get-url origin)" != *"$TARGET"* ]]; then
  echo "Target origin is not $TARGET" >&2
  exit 1
fi

# Never replace preexisting refs. This is deliberately an import, not a sync.
if [[ -n "$(git -C "$WORKSPACE" ls-remote --heads origin upstream-source develop)" ]]; then
  echo "Import target branch already exists. Refusing to overwrite it." >&2
  exit 1
fi

BOOTSTRAP_SHA="$(git -C "$WORKSPACE" rev-parse HEAD)"
echo "Bootstrapping from target main $BOOTSTRAP_SHA"
echo "Reading upstream $UPSTREAM_SHA (immutable checkpoint)"

git clone --quiet --single-branch --no-tags --branch main "$UPSTREAM_URL" "$SRC"
git -C "$SRC" cat-file -e "$UPSTREAM_SHA^{commit}"
git -C "$SRC" switch -C main "$UPSTREAM_SHA"
git -C "$SRC" remote remove origin

# Filter EVERY reachable commit; not just the latest working tree.
# Includes source code, build scripts and docs, but no JSON/data or APK/art.
git -C "$SRC" filter-repo --force \
  --path-regex '^source/.*\.(py|js|cjs|java|kt|rs|gradle|toml|lock|ps1|sh|bat|cmd|md|xml|properties|html|css|yml|yaml|ini|c|h|cpp|hpp)$'

python "$WORKSPACE/scripts/check_public_tree.py" --repo "$SRC" --history --require-source

# Stage the rewritten history ONLY in the local checked-out target clone.
# Using a local Git transfer means no public branch is exposed before audit.
git -C "$SRC" push --quiet "$WORKSPACE" HEAD:refs/heads/upstream-source

git -C "$WORKSPACE" config user.name "FFBE-Custom source import"
git -C "$WORKSPACE" config user.email "actions@users.noreply.github.com"
git -C "$WORKSPACE" switch -c develop upstream-source
git -C "$WORKSPACE" merge --allow-unrelated-histories --no-edit --no-ff \
  -m "Merge source-only upstream history with public development infrastructure" "$BOOTSTRAP_SHA"

# Re-audit the merged development branch, including all history.
python "$WORKSPACE/scripts/check_public_tree.py" --repo "$WORKSPACE" --history --require-source

# Parse source without installing dependencies or executing game code.
python -m compileall -q "$WORKSPACE/source"
while IFS= read -r -d '' file; do
  node --check "$file"
done < <(find "$WORKSPACE/source" -type f \\( -name '*.js' -o -name '*.cjs' \\) -print0)
echo "PASS: source-only Python and JavaScript syntax checks"

echo "Filtered upstream commit: $(git -C "$WORKSPACE" rev-parse upstream-source)"
echo "Development commit:      $(git -C "$WORKSPACE" rev-parse develop)"
echo "Verifying branch push is new (no force; no release tags)"
git -C "$WORKSPACE" push --atomic origin \
  refs/heads/upstream-source:refs/heads/upstream-source \
  refs/heads/develop:refs/heads/develop

echo "IMPORT COMPLETE: upstream-source and develop published; main untouched"
