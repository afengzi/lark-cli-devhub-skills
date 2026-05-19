from __future__ import annotations

import subprocess
from typing import Any

from .io import parse_json_output


def run_lark(args: list[str], *, check: bool = True) -> tuple[dict[str, Any], str]:
    cmd = ["lark-cli", *args]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"lark-cli exited {result.returncode}"
        raise RuntimeError(message)
    return parse_json_output(result.stdout), result.stdout


def run_lark_with_input(args: list[str], stdin: str, *, check: bool = True) -> tuple[dict[str, Any], str]:
    cmd = ["lark-cli", *args]
    result = subprocess.run(cmd, text=True, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"lark-cli exited {result.returncode}"
        raise RuntimeError(message)
    return parse_json_output(result.stdout), result.stdout
