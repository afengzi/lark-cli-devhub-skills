from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import (
    command_cleanup_relation_fields,
    command_preflight,
    command_provision,
    command_report_draft,
    command_search,
    command_whiteboard_draft,
)
from .hooks import command_hook_check
from .records import command_receipt, command_sync_outbox, record_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lark CLI Dev Hub helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight").set_defaults(func=command_preflight)

    provision = sub.add_parser("provision")
    provision.add_argument("--schema", required=True)
    provision.add_argument("--seed", required=True)
    provision.add_argument("--views", default="")
    provision.set_defaults(func=command_provision)

    cleanup = sub.add_parser("cleanup-relation-fields")
    cleanup.add_argument("--dry-run", action="store_true")
    cleanup.set_defaults(func=command_cleanup_relation_fields)

    search = sub.add_parser("search")
    search.add_argument("--project", required=True)
    search.add_argument("--query", required=True)
    search.set_defaults(func=command_search)

    report = sub.add_parser("report-draft")
    report.add_argument("--kind", choices=["daily", "weekly", "release"], required=True)
    report.add_argument("--project", required=True)
    report.add_argument("--records", required=True)
    report.add_argument("--wiki", action="store_true", help="write the report draft into project Wiki and index it in Artifacts")
    report.set_defaults(func=command_report_draft)

    board = sub.add_parser("whiteboard-draft")
    board.add_argument("--kind", required=True)
    board.add_argument("--project", required=True)
    board.add_argument("--summary", required=True)
    board.set_defaults(func=command_whiteboard_draft)

    record_tables = [
        ("record-task", "Tasks"),
        ("record-bugfix", "Bugfixes"),
        ("record-pitfall", "Pitfalls"),
        ("record-playbook", "Playbooks"),
        ("record-ai-run", "AI Runs"),
        ("record-release", "Releases"),
        ("record-decision", "Decisions"),
        ("record-artifact", "Artifacts"),
        ("record-project-fact", "Project Facts"),
    ]
    for name, table in record_tables:
        item = sub.add_parser(name)
        item.add_argument("--payload", required=True)
        item.add_argument("--wiki", action="store_true", help="also write a long-form Wiki doc and Artifacts index when supported")
        item.set_defaults(func=lambda ns, n=name, t=table: record_command(n, t, Path(ns.payload), Path.cwd(), write_wiki=ns.wiki))

    receipt = sub.add_parser("receipt")
    receipt.add_argument("--kind", required=True)
    receipt.add_argument("--record-url", required=True)
    receipt.add_argument("--summary", required=True)
    receipt.set_defaults(func=command_receipt)

    hook = sub.add_parser("hook-check")
    hook.add_argument("--command", required=True)
    hook.add_argument("--cwd", required=True)
    hook.set_defaults(func=command_hook_check)

    sync = sub.add_parser("sync-outbox")
    sync.add_argument("--cwd", required=True)
    sync.set_defaults(func=command_sync_outbox)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"devhub error: {exc}", file=sys.stderr)
        return 1
