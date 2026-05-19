from __future__ import annotations

from typing import Any


def _titles(records: list[dict[str, Any]], fallback_key: str = "AI Summary") -> list[str]:
    values: list[str] = []
    for record in records:
        title = record.get("Title") or record.get(fallback_key) or ""
        if title:
            values.append(str(title))
    return values


def _bullets(values: list[str]) -> str:
    if not values:
        return "- No records found."
    return "\n".join(f"- {value}" for value in values)


def draft_report(kind: str, project: str, records: dict[str, list[dict[str, Any]]]) -> str:
    if kind == "daily":
        return "\n".join(
            [
                f"# Daily Report: {project}",
                "",
                "## Completed Work",
                _bullets(_titles(records.get("Tasks", [])) + _titles(records.get("Bugfixes", []))),
                "",
                "## Blockers",
                _bullets([str(item.get("Blocker")) for item in records.get("Tasks", []) if item.get("Blocker")]),
                "",
                "## Next Actions",
                _bullets([str(item.get("Next Action")) for item in records.get("Tasks", []) if item.get("Next Action")]),
                "",
            ]
        )
    if kind == "weekly":
        return "\n".join(
            [
                f"# Weekly Report: {project}",
                "",
                "## Completed Work",
                _bullets(_titles(records.get("Tasks", [])) + _titles(records.get("Bugfixes", []))),
                "",
                "## AI Evidence",
                _bullets(_titles(records.get("AI Runs", []), "Verification Result")),
                "",
                "## Releases",
                _bullets(_titles(records.get("Releases", []), "Summary")),
                "",
                "## Decisions",
                _bullets(_titles(records.get("Decisions", []), "Decision")),
                "",
                "## Risks And Next Week",
                "- Review open blockers, failed CI records, and stale Project Facts.",
                "",
            ]
        )
    if kind == "release":
        rollback = [str(item.get("Rollback Notes")) for item in records.get("Releases", []) if item.get("Rollback Notes")]
        return "\n".join(
            [
                f"# Release Brief: {project}",
                "",
                "## Included Releases",
                _bullets(_titles(records.get("Releases", []), "Summary")),
                "",
                "## Related Bugfixes",
                _bullets(_titles(records.get("Bugfixes", []))),
                "",
                "## Verification",
                _bullets([str(item.get("Verification Result")) for item in records.get("Releases", []) if item.get("Verification Result")]),
                "",
                "## Rollback Notes",
                _bullets(rollback),
                "",
            ]
        )
    raise ValueError(f"unsupported report kind: {kind}")
