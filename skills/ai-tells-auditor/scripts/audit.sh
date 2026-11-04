#!/usr/bin/env bash
# Run the ai-tells-auditor Vale config on files, or on stdin when no file is given.
#
#   audit.sh draft.md docs/            lint files and directories
#   pbpaste | audit.sh                 lint text from stdin, as Markdown
#   audit.sh --json draft.md           Vale's JSON instead of one line per finding
#   audit.sh --min=warning draft.md    skip suggestions
#
# Exit codes: 0 no errors, 1 at least one error-level finding (Vale's own),
# 2 Vale failed, 3 Vale is not installed.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$SKILL_DIR/.vale.ini"
STYLES="$SKILL_DIR/styles"
TEMPLATE="$STYLES/config/templates/ai-tells-agent.tmpl"
VALE="${VALE:-$(command -v vale || true)}"

if [ -z "$VALE" ]; then
  echo "vale is not installed. Install it with 'brew install vale' (macOS) or see https://vale.sh/docs/install, then rerun." >&2
  exit 3
fi

# The third-party packs are fetched, not committed. Sync when any is missing,
# e.g. on first run or after a plugin update replaced the skill folder.
for pack in ai-tells proselint write-good Microsoft Google; do
  if [ ! -d "$STYLES/$pack" ] || [ ! -f "$TEMPLATE" ]; then
    echo "Fetching Vale packs (first run)..." >&2
    "$VALE" --config "$CONFIG" sync >&2 || { echo "vale sync failed; check network access." >&2; exit 2; }
    break
  fi
done

output="$TEMPLATE"
args=()
for a in "$@"; do
  case "$a" in
    --json) output=JSON ;;
    --min=*) args+=("--minAlertLevel=${a#--min=}") ;;
    -*) args+=("$a") ;;
    *)
      # Vale skips a missing path without a word, which reads as "no findings".
      [ -e "$a" ] || { echo "No such file or directory: $a" >&2; exit 2; }
      args+=("$a") ;;
  esac
done

set +e
if [ ${#args[@]} -eq 0 ] || { [ ${#args[@]} -eq 1 ] && [[ "${args[0]}" == --minAlertLevel=* ]]; }; then
  "$VALE" --config "$CONFIG" --output="$output" --ext=.md "${args[@]+"${args[@]}"}"
else
  "$VALE" --config "$CONFIG" --output="$output" "${args[@]}"
fi
code=$?
set -e
[ $code -le 1 ] || exit 2
exit $code
