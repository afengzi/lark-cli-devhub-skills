from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import command_preflight, command_provision, command_search
from .hooks import command_hook_check
from .records import command_receipt, command_sync_outbox, record_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lark CLI Dev Hub helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight").set_defaults(func=command_preflight)

    provision = sub.add_parser("provision")
    provision.add_argument("--schema", required=True)
    provision.add_argument("--seed", required=True)
    provision.set_defaults(func=command_provision)

    search = sub.add_parser("search")
    search.add_argument("--project", required=True)
    search.add_argument("--query", required=True)
    search.set_defaults(func=command_search)

    for name, table in [("record-bugfix", "Bugfixes"), ("record-ai-run", "AI Runs"), ("record-release", "Releases")]:
        item = sub.add_parser(name)
        item.add_argument("--payload", required=True)
        item.set_defaults(func=lambda ns, n=name, t=table: record_command(n, t, Path(ns.payload), Path.cwd()))

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
