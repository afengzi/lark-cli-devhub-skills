# Automation Patterns

## Manual Command

Manual command is the reliable baseline. It must work even when hooks, GitHub Actions, cron, and Whiteboard tooling are not configured.

## Local Git Hook

Use local hooks to remind users about knowledge writeback. Hooks may warn or block depending on mode, but they must accept receipts, outbox items, or `# kb-skip: reason`.

## GitHub Action

Use GitHub Actions to map PR and CI events to Dev Hub record writes. A completed workflow run is not write success; receipt or outbox evidence is required.

## Cron

Use cron or scheduled workflows to generate report drafts. Publish drafts only after explicit approval.

## Whiteboard Workflow

Use draft and dry-run first. Final boards must be linked through Artifacts records.
