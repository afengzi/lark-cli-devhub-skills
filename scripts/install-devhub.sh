#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEVHUB_HOME="${DEVHUB_HOME:-$HOME/.codex/devhub}"
SKILLS_HOME="${SKILLS_HOME:-$HOME/.agents/skills}"
SKILL_SET="${DEVHUB_SKILLS:-all}"
SHOW_AUTH_GUIDE=1

usage() {
  cat <<'EOF'
Usage: scripts/install-devhub.sh [options]

Options:
  --skills <set>       all | core | workflow | domain | comma-separated skill names
                       default: all
  --list-skills        show selectable skill groups and exit
  --no-auth-guide      omit lark-cli auth guidance from the final output
  -h, --help           show this help

Examples:
  ./scripts/install-devhub.sh
  ./scripts/install-devhub.sh --skills core
  ./scripts/install-devhub.sh --skills workflow
  ./scripts/install-devhub.sh --skills lark-cli-devhub,lark-cli-devhub-code-loop
EOF
}

WORKFLOW_SKILLS=(
  lark-cli-devhub
  lark-cli-devhub-code-loop
  lark-cli-devhub-report-loop
  lark-cli-devhub-pr-writeback
  lark-cli-devhub-whiteboard-loop
)

CORE_SKILLS=(
  "${WORKFLOW_SKILLS[@]}"
  lark-cli-devhub-base
  lark-cli-devhub-docs-wiki
  lark-cli-devhub-taskflow
  lark-cli-devhub-whiteboard
)

DOMAIN_SKILLS=(
  lark-cli-devhub-base
  lark-cli-devhub-docs-wiki
  lark-cli-devhub-taskflow
  lark-cli-devhub-whiteboard
  lark-cli-devhub-drive
  lark-cli-devhub-sheets
  lark-cli-devhub-calendar
  lark-cli-devhub-communications
  lark-cli-devhub-meetings
  lark-cli-devhub-approvals-okr
  lark-cli-devhub-slides
  lark-cli-devhub-events
)

list_skills() {
  echo "workflow:"
  printf '  %s\n' "${WORKFLOW_SKILLS[@]}"
  echo "core:"
  printf '  %s\n' "${CORE_SKILLS[@]}"
  echo "domain:"
  printf '  %s\n' "${DOMAIN_SKILLS[@]}"
  echo "all:"
  find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | sed 's/^/  /'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --skills)
      if [ "$#" -lt 2 ]; then
        echo "Missing value for --skills." >&2
        usage >&2
        exit 2
      fi
      SKILL_SET="${2:-}"
      shift 2
      ;;
    --list-skills)
      list_skills
      exit 0
      ;;
    --no-auth-guide)
      SHOW_AUTH_GUIDE=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

selected_skills() {
  case "$SKILL_SET" in
    all)
      find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
      ;;
    core)
      printf '%s\n' "${CORE_SKILLS[@]}"
      ;;
    workflow)
      printf '%s\n' "${WORKFLOW_SKILLS[@]}"
      ;;
    domain)
      printf '%s\n' "${DOMAIN_SKILLS[@]}"
      ;;
    *)
      printf '%s\n' "$SKILL_SET" | tr ',' '\n' | sed '/^$/d'
      ;;
  esac
}

SELECTED_SKILLS=()
while IFS= read -r skill; do
  SELECTED_SKILLS+=("$skill")
done < <(selected_skills)

if [ "${#SELECTED_SKILLS[@]}" -eq 0 ]; then
  echo "No skills selected." >&2
  exit 2
fi

mkdir -p "$DEVHUB_HOME/bin" "$DEVHUB_HOME/templates" "$SKILLS_HOME"

install -m 755 "$ROOT/scripts/devhub.py" "$DEVHUB_HOME/bin/devhub.py"
install -m 755 "$ROOT/scripts/kb-gate.sh" "$DEVHUB_HOME/bin/kb-gate.sh"
rm -rf "$DEVHUB_HOME/bin/devhub_lib"
cp -R "$ROOT/scripts/devhub_lib" "$DEVHUB_HOME/bin/devhub_lib"
cp "$ROOT/templates/base-schema.json" "$DEVHUB_HOME/templates/base-schema.json"
cp "$ROOT/templates/base-views.json" "$DEVHUB_HOME/templates/base-views.json"
cp "$ROOT/templates/seed.example.json" "$DEVHUB_HOME/templates/seed.example.json"
cp "$ROOT/templates/config.example.json" "$DEVHUB_HOME/templates/config.example.json"
cp "$ROOT/templates/report-daily.md" "$DEVHUB_HOME/templates/report-daily.md"
cp "$ROOT/templates/report-weekly.md" "$DEVHUB_HOME/templates/report-weekly.md"
cp "$ROOT/templates/report-release.md" "$DEVHUB_HOME/templates/report-release.md"
cp "$ROOT/templates/whiteboard-draft.md" "$DEVHUB_HOME/templates/whiteboard-draft.md"
rm -rf "$DEVHUB_HOME/templates/wiki" "$DEVHUB_HOME/templates/whiteboards"
cp -R "$ROOT/templates/wiki" "$DEVHUB_HOME/templates/wiki"
cp -R "$ROOT/templates/whiteboards" "$DEVHUB_HOME/templates/whiteboards"

installed_skills=()
for name in "${SELECTED_SKILLS[@]}"; do
  skill_dir="$ROOT/skills/$name"
  if [ ! -d "$skill_dir" ]; then
    echo "Unknown skill: $name" >&2
    echo "Run: ./scripts/install-devhub.sh --list-skills" >&2
    exit 2
  fi
  target="$SKILLS_HOME/$name"
  if [ -L "$target" ]; then
    rm "$target"
  elif [ -e "$target" ]; then
    echo "skip existing non-symlink skill: $target"
    continue
  fi
  ln -s "$skill_dir" "$target"
  installed_skills+=("$target")
done

installed_skill_lines() {
  if [ "${#installed_skills[@]}" -eq 0 ]; then
    echo "  none"
    return
  fi
  printf '  %s\n' "${installed_skills[@]}"
}

mkdir -p ".devhub/receipts" ".devhub/outbox"

cat <<EOF
Lark CLI Dev Hub installed.

Helper:
  $DEVHUB_HOME/bin/devhub.py

Templates:
  $DEVHUB_HOME/templates/base-schema.json
  $DEVHUB_HOME/templates/base-views.json
  $DEVHUB_HOME/templates/seed.example.json
  $DEVHUB_HOME/templates/report-weekly.md
  $DEVHUB_HOME/templates/whiteboard-draft.md
  $DEVHUB_HOME/templates/wiki/
  $DEVHUB_HOME/templates/whiteboards/

Skills selected:
  $SKILL_SET

Skills installed:
$(installed_skill_lines)

Next:
  python3 "$DEVHUB_HOME/bin/devhub.py" preflight
  python3 "$DEVHUB_HOME/bin/devhub.py" provision \
    --schema "$DEVHUB_HOME/templates/base-schema.json" \
    --seed "$DEVHUB_HOME/templates/seed.example.json" \
    --views "$DEVHUB_HOME/templates/base-views.json"
  python3 "$DEVHUB_HOME/bin/devhub.py" search --project "$(basename "$PWD")" --query "area symptom"
  python3 "$DEVHUB_HOME/bin/devhub.py" report-draft --kind weekly --project "$(basename "$PWD")" --records "$DEVHUB_HOME/templates/seed.example.json"
EOF

if [ "$SHOW_AUTH_GUIDE" -eq 1 ]; then
  cat <<'EOF'

Lark CLI auth setup:
  lark-cli doctor --offline
  lark-cli auth status --verify
  lark-cli auth login --domain base,wiki,docs --recommend
  lark-cli auth scopes --format pretty

For additional workflows, request only the domains you enable:
  lark-cli auth login --domain task,drive,im,calendar,sheets,minutes --recommend

To inspect exact scopes before requesting them:
  lark-cli schema <service.resource.method> --format pretty
  lark-cli auth check --scope "<space-separated scopes>"

For headless agent sessions:
  lark-cli auth login --domain base,wiki,docs --recommend --no-wait --json
  # after browser approval:
  lark-cli auth login --device-code "<device_code>"
EOF
fi
