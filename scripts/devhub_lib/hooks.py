from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import load_config, repo_runtime_dir


def is_git_commit(cmd: str) -> bool:
    return "git commit" in cmd


def is_git_push(cmd: str) -> bool:
    return "git push" in cmd


def targets_main(cmd: str, cwd: Path) -> bool:
    if " main" in cmd or " master" in cmd or ":main" in cmd or ":master" in cmd:
        return True
    stripped = cmd.split("#", 1)[0]
    tokens = stripped.split()
    if len(tokens) <= 3:
        branch = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return branch.stdout.strip() in {"main", "master"}
    return False


def has_runtime_evidence(cwd: Path) -> bool:
    receipts = repo_runtime_dir(cwd, "receipt_dir")
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    has_receipt = any(receipts.glob("*.json")) if receipts.exists() else False
    has_outbox = any(outbox.glob("*.json")) if outbox.exists() else False
    return has_receipt or has_outbox


def command_hook_check(args: Any) -> int:
    config = load_config()
    mode = config.get("mode", "shadow")
    cmd = args.command
    cwd = Path(args.cwd)
    if not is_git_commit(cmd) and not is_git_push(cmd):
        return 0
    needs_kb = False
    reason = ""
    if is_git_push(cmd) and targets_main(cmd, cwd):
        needs_kb = True
        reason = "push to main/master should have a Release or Bugfix writeback"
    elif is_git_commit(cmd) and any(word in cmd.lower() for word in ["fix", "bug", "release"]):
        needs_kb = True
        reason = "bugfix/release commit should have a knowledge-base writeback"
    if not needs_kb:
        return 0
    if "# kb-updated" in cmd or "# kb-skip:" in cmd or has_runtime_evidence(cwd):
        return 0
    message = f"Dev Hub knowledge writeback missing: {reason}. Add # kb-updated after writing Feishu, or # kb-skip: reason for a justified skip."
    if mode == "enforced":
        print(f"BLOCKED: {message}", file=sys.stderr)
        return 2
    print(f"Shadow Mode: {message}", file=sys.stderr)
    return 0
