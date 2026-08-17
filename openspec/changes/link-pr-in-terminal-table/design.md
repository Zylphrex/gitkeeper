## Context

See `proposal.md` for motivation. The terminal table rendered by `render_pull_requests_table` in `gitkeeper/ui/table.py` receives a list of `ScoredPullRequest` objects containing `PullRequestData` which already provides `pr.url` fetched by GitHub GraphQL. Currently, the column formats the number strictly as `f"#{pr.number}"`.

## Goals / Non-Goals

**Goals:**
- Render `#<number>` as a terminal hyperlink to `pr.url` using Rich console markup (`[link=<url>]#<number>[/link]`).
- Preserve table visual width and existing styling.
- Handle missing or empty `pr.url` gracefully by rendering `#<number>`.

**Non-Goals:**
- Adding a standalone URL column that would consume horizontal space.
- Adding interactive selector / keyboard navigation (deferred to future feature if desired).

## Decisions

### 1. Anchor hyperlink to the PR number string
- **Choice**: Format as `f"[link={pr.url}]#{pr.number}[/link]"` when `pr.url` is present.
- **Rationale**: Modern terminal emulators natively support OSC 8 hyperlinks. It preserves concise table columns and aligns with user expectations for terminal UIs.
- **Alternative considered**: Dedicated URL column. Rejected because long URLs disrupt table formatting in narrow terminal viewports.

## Risks / Trade-offs

- **[Risk] Terminal emulator lacks OSC 8 hyperlink support** → **Mitigation**: Rich automatically degrades gracefully to plain text `#<number>` when the terminal does not support OSC 8 hyperlinks or when colors/formatting are disabled.
