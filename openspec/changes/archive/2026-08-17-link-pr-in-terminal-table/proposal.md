## Why

When viewing the prioritized review queue via `gitkeeper list` / `gitkeeper queue`, users currently only see a plain text PR number (e.g., `#123`). To actually review the PR, they have to manually construct or search for the URL in their browser. Linking the PR number directly to the pull request URL via terminal hyperlinks (OSC 8) allows reviewers to jump directly into code review with a single click while maintaining a clean, compact table layout.

## What Changes

- Format PR numbers in the terminal table as clickable terminal hyperlinks (OSC 8) targeting the PR URL (`pr.url`).
- Gracefully fall back to plain text PR numbers (`#<number>`) when no URL is available.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `terminal-interface`: Update queue rendering requirements to specify that PR numbers in the table link directly to the PR URL via terminal hyperlinks.

## Impact

- **Affected code**: `gitkeeper/ui/table.py` and UI table rendering tests.
- **Dependencies**: Uses Rich's built-in `[link=URL]text[/link]` markup.
- **Backwards Compatibility**: Fully backwards compatible. Terminals without OSC 8 support render the plain text as before.
