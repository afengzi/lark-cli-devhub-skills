from __future__ import annotations


def draft_whiteboard(kind: str, project: str, summary: str) -> str:
    return "\n".join(
        [
            f"# Whiteboard Draft: {project}",
            "",
            f"Kind: {kind}",
            "",
            "## Purpose",
            summary,
            "",
            "## Diagram Nodes",
            "- Current system",
            "- Changed component",
            "- Related Project Facts",
            "- Related Decisions",
            "- Related Artifacts",
            "",
            "## Links To Add After Approval",
            "- Create an Artifacts record for the final board or fallback Doc diagram.",
            "- Link related Bugfixes, AI Runs, Decisions, and Project Facts.",
            "",
            "## Safety",
            "- Draft first.",
            "- Run dry-run when the Whiteboard tool supports it.",
            "- Write final board only after explicit approval.",
            "",
        ]
    )
