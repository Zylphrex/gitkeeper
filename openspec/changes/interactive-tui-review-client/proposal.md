## Why

Currently, GitKeeper outputs a static CLI table with clickable URLs, forcing developers to leave the terminal and context-switch to the GitHub web UI to inspect diffs, leave comments, approve, or triage pull requests. By replacing the static table with a full-screen interactive Textual TUI, developers can complete the entire review and triage lifecycle locally without disrupting their workflow.

## What Changes

- **BREAKING**: Replaced all CLI subcommands and static table output with a single direct `gitkeeper` entrypoint that launches the interactive full-screen Textual TUI.
- Added a multi-pane TUI layout with ranked PR navigation, PR metadata overview, and score rationale breakdown.
- Added an in-TUI diff viewer allowing developers to view unified diffs and navigate file changes directly.
- Added line-by-line inline commenting on diffs and top-level review comments.
- Added review submission actions (Approve, Request Changes, Comment) via GitHub API mutations.
- Added manual refresh capability to re-fetch and re-score review requests on demand.
- Expanded the GitHub client with mutations for submitting pull request reviews and queries for fetching unified file diffs.

## Capabilities

### New Capabilities
- `tui-review-client`: Interactive full-screen terminal user interface (Textual) providing ranked PR queue browsing, in-app file diff viewer, inline and top-level commenting, review mutations (Approve/Request Changes/Comment), and manual queue refresh.

### Modified Capabilities
- `terminal-interface`: Update the CLI entrypoint to launch the full-screen interactive TUI rather than printing static one-shot tables.
- `github-client`: Add support for fetching PR diffs and submitting reviews (with optional inline comments) via GitHub API.

## Impact

- **CLI Interface**: `gitkeeper` CLI launches the full-screen Textual application by default.
- **Dependencies**: Added `textual>=0.50.0` to project dependencies.
- **GitHub API**: Requires `write` or `pull_requests:write` permissions for review submission mutations.
