#!/usr/bin/env bash
# Feishu Dev Hub knowledge-base gate.
# Shadow Mode by default: checks git commit/push commands and warns when a
# knowledge-base writeback marker, receipt, or outbox is missing.

set -euo pipefail

DEVHUB_HOME="${DEVHUB_HOME:-$HOME/.codex/devhub}"
input=$(cat)
cmd=$(echo "$input" | python3 -c "import json,sys
try:
    print(json.load(sys.stdin).get('tool_input',{}).get('command',''))
except Exception:
    pass" 2>/dev/null)

if ! echo "$cmd" | grep -qE '(^|[^a-zA-Z0-9_-])git[[:space:]]+(commit|push)([[:space:]]|$)'; then
  exit 0
fi

python3 "$DEVHUB_HOME/bin/devhub.py" hook-check --command "$cmd" --cwd "$(pwd)"
