## 1. Dependencies and Client Extensions

- [x] 1.1 Add `textual>=0.50.0` dependency to `pyproject.toml`
- [x] 1.2 Implement PR diff retrieval in `GitHubGraphQLClient` / REST client (`get_pull_request_diff`)
- [x] 1.3 Implement unified diff parser to extract files, line numbers, and diff hunks
- [x] 1.4 Implement GitHub review submission mutation (`add_pull_request_review`) in `GitHubGraphQLClient`

## 2. Textual TUI Core & Widgets

- [x] 2.1 Create base Textual App skeleton with layout, header, footer, and styling
- [x] 2.2 Implement `PRListView` widget with ranked scoring badges and active/ambient tabs
- [x] 2.3 Implement `PROverviewView` widget showing metadata, score breakdown, and markdown body
- [x] 2.4 Implement `PRDiffView` widget with file navigation tree and syntax-highlighted diff viewer
- [x] 2.5 Implement `InlineCommentModal` for adding line-level comments on diff lines
- [x] 2.6 Implement `SubmitReviewModal` for review event selection (Approve, Request Changes, Comment) and summary submission

## 3. Review Workflow & CLI Integration

- [x] 3.1 Wire local review draft state management and batched submission in the TUI
- [x] 3.2 Wire manual refresh action (`r`) to re-fetch and re-rank PRs dynamically
- [x] 3.3 Replace CLI entrypoint in `gitkeeper/cli.py` to launch the Textual TUI app directly upon running `gitkeeper` with no subcommands
- [x] 3.4 Remove obsolete subcommands and table formatting code in favor of direct TUI launching

## 4. Testing & Verification

- [x] 4.1 Add unit tests for unified diff parser and hunk calculations
- [x] 4.2 Add unit tests for review mutation payload generation and error handling
- [x] 4.3 Add test coverage for TUI widgets and navigation bindings
- [x] 4.4 Verify end-to-end flow manually using mock/fixture PR data
