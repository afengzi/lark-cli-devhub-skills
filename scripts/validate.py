#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_PATTERNS = [
    (re.compile(r"/Users/[^/\s]+"), "absolute macOS user path"),
    (re.compile(r"https://[^/\s]*feishu\.cn/(base|wiki|docx|docs|sheets)/[A-Za-z0-9]{10,}"), "concrete Feishu resource URL"),
    (re.compile(r"\b(app_secret|access_token|private_key|gho_[A-Za-z0-9_]+)\b", re.IGNORECASE), "secret-like marker"),
]


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path}: unterminated YAML frontmatter")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def validate_skills() -> list[str]:
    errors: list[str] = []
    for skill in sorted((ROOT / "skills").iterdir()):
        if not skill.is_dir():
            continue
        skill_file = skill / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"{skill}: missing SKILL.md")
            continue
        try:
            fields = parse_frontmatter(skill_file)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        name = fields.get("name", "")
        description = fields.get("description", "")
        if name != skill.name:
            errors.append(f"{skill_file}: name must match directory ({skill.name})")
        if not NAME_RE.match(name):
            errors.append(f"{skill_file}: invalid name {name!r}")
        if not description:
            errors.append(f"{skill_file}: missing description")
        if len(description) > 1024:
            errors.append(f"{skill_file}: description exceeds 1024 chars")
    return errors


def scan_forbidden() -> list[str]:
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, label in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)} contains forbidden content: {label}")
    return errors


def compile_python() -> list[str]:
    errors: list[str] = []
    for path in [ROOT / "scripts" / "devhub.py", ROOT / "scripts" / "validate.py"]:
        result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            errors.append(result.stderr.strip())
    return errors


def main() -> int:
    errors = validate_skills() + scan_forbidden() + compile_python()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
