#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEVHUB_HOME="${DEVHUB_HOME:-$HOME/.codex/devhub}"
SKILLS_HOME="${SKILLS_HOME:-$HOME/.agents/skills}"

mkdir -p "$DEVHUB_HOME/bin" "$DEVHUB_HOME/templates" "$SKILLS_HOME"

install -m 755 "$ROOT/scripts/devhub.py" "$DEVHUB_HOME/bin/devhub.py"
install -m 755 "$ROOT/scripts/kb-gate.sh" "$DEVHUB_HOME/bin/kb-gate.sh"
rm -rf "$DEVHUB_HOME/bin/devhub_lib"
cp -R "$ROOT/scripts/devhub_lib" "$DEVHUB_HOME/bin/devhub_lib"
cp "$ROOT/templates/base-schema.json" "$DEVHUB_HOME/templates/base-schema.json"
cp "$ROOT/templates/seed.example.json" "$DEVHUB_HOME/templates/seed.example.json"
cp "$ROOT/templates/config.example.json" "$DEVHUB_HOME/templates/config.example.json"
cp "$ROOT/templates/report-daily.md" "$DEVHUB_HOME/templates/report-daily.md"
cp "$ROOT/templates/report-weekly.md" "$DEVHUB_HOME/templates/report-weekly.md"
cp "$ROOT/templates/report-release.md" "$DEVHUB_HOME/templates/report-release.md"
cp "$ROOT/templates/whiteboard-draft.md" "$DEVHUB_HOME/templates/whiteboard-draft.md"

for skill_dir in "$ROOT"/skills/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  target="$SKILLS_HOME/$name"
  if [ -L "$target" ]; then
    rm "$target"
  elif [ -e "$target" ]; then
    echo "skip existing non-symlink skill: $target"
    continue
  fi
  ln -s "$skill_dir" "$target"
done

mkdir -p ".devhub/receipts" ".devhub/outbox"

cat <<EOF
Lark CLI Dev Hub installed.

Helper:
  $DEVHUB_HOME/bin/devhub.py

Templates:
  $DEVHUB_HOME/templates/base-schema.json
  $DEVHUB_HOME/templates/seed.example.json
  $DEVHUB_HOME/templates/report-weekly.md
  $DEVHUB_HOME/templates/whiteboard-draft.md

Skills:
  $SKILLS_HOME/lark-cli-devhub
  $SKILLS_HOME/lark-cli-devhub-code-loop
  $SKILLS_HOME/lark-cli-devhub-report-loop
  $SKILLS_HOME/lark-cli-devhub-pr-writeback
  $SKILLS_HOME/lark-cli-devhub-whiteboard-loop
  $SKILLS_HOME/lark-cli-devhub-base
  $SKILLS_HOME/lark-cli-devhub-docs-wiki
  $SKILLS_HOME/lark-cli-devhub-taskflow
  $SKILLS_HOME/lark-cli-devhub-whiteboard

Next:
  python3 "$DEVHUB_HOME/bin/devhub.py" preflight
  python3 "$DEVHUB_HOME/bin/devhub.py" provision \
    --schema "$DEVHUB_HOME/templates/base-schema.json" \
    --seed "$DEVHUB_HOME/templates/seed.example.json"
  python3 "$DEVHUB_HOME/bin/devhub.py" search --project "$(basename "$PWD")" --query "area symptom"
  python3 "$DEVHUB_HOME/bin/devhub.py" report-draft --kind weekly --project "$(basename "$PWD")" --records "$DEVHUB_HOME/templates/seed.example.json"
EOF
