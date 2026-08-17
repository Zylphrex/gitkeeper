## Context

Currently, GitKeeper uses `Typer` and `Rich` to output a static table to the terminal. To achieve a seamless local review workflow as outlined in `proposal.md`, we will replace the static table with a full-screen reactive terminal user interface (TUI) built using `Textual`.

## Goals / Non-Goals

**Goals:**
- Provide a responsive full-screen TUI for navigating prioritized PR queues.
- Render PR markdown overviews and score breakdown explanations.
- Fetch and display syntax-highlighted unified diffs for modified files.
- Enable inline code comments on diff lines and top-level review notes.
- Support submitting PR reviews directly to GitHub (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).
- Provide manual refresh (`r`) to update the queue.
- Make the interactive TUI the sole, standard entrypoint for GitKeeper.

**Non-Goals:**
- Supporting subcommands (e.g. `queue`, `list`); running `gitkeeper` will directly start the TUI.
- Supporting complex rich git conflict resolution or in-app merge tools (can be done in external git/editor).
- Replacing code editors for authoring large code modifications.
- Implementing automatic background interval polling (manual refresh only for predictability and rate limits).

## Decisions

### 1. Framework: Textual
- **Decision**: Adopt `textual>=0.50.0` for all UI components.
- **Rationale**: Textual natively builds upon `Rich` (which GitKeeper already uses), has first-class async support for non-blocking GitHub API requests, and provides high-quality widgets (DataTable, Tree, MarkdownViewer, TextArea, Modals).
- **Alternatives Considered**:
  - *Prompt-toolkit / InquirerPy*: Good for simple step-by-step prompts, but clumsy for multi-pane split-screen layouts and simultaneous diff inspection.
  - *Curses / Urwid*: Outdated APIs, poor styling support, difficult to integrate with existing Rich renderables.

### 2. TUI View Hierarchy & Component Architecture
- **Decision**: Structure the UI using a responsive split layout:
  - `Header` & `Footer` (with keybindings).
  - `Left Pane`: `PRListView` (ranked list of PRs, tabs for Active Queue and Ambient/Hidden PRs).
  - `Right Pane`: Tabbed container:
    - Tab 1: `PROverviewView` (score rationale banner, PR metadata, and markdown body).
    - Tab 2: `PRDiffView` (file tree selector + unified diff viewer with cursor line tracking).
  - `Modals`:
    - `InlineCommentModal`: Text input targeting a specific file and line.
    - `SubmitReviewModal`: Review event selector (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`) + summary body input.
- **Alternatives Considered**:
  - *Single switching screen*: Switching screens between List and Diff loses contextual comparison; a split/tab layout maintains orientation.

### 3. Diff Retrieval & Parsing Strategy
- **Decision**: Fetch raw unified diff via GitHub REST API endpoint (`GET /repos/{owner}/{repo}/pulls/{number}` with header `Accept: application/vnd.github.v3.diff`) and parse it into file-level hunk blocks with original/new line number mappings.
- **Rationale**: GraphQL does not supply raw patch text for full PRs cleanly without complex pagination over files/patches; GitHub REST diff endpoint gives the exact unified diff in one HTTP request.

### 4. Review Mutation & Draft Batching
- **Decision**: Draft comments locally in memory per PR session, and submit them in a single batch using GitHub GraphQL `addPullRequestReview` mutation when the user chooses `[Submit Review]` (or one-click approve with empty comments).
- **Rationale**: Batching prevents creating spammy single-comment notifications on GitHub and allows reviewers to review multiple files before publishing feedback.

## Risks / Trade-offs

- **[Risk] Large Diffs & Performance**: PRs with hundreds of changed files or thousands of lines could slow down terminal rendering.
  - *Mitigation*: Parse diffs lazily per file, truncate individual files over 2,000 lines with a notice, and render diff lines inside a virtual scrolling widget.
- **[Risk] Token Permissions**: Submitting reviews requires GitHub write permissions on pull requests.
  - *Mitigation*: Display clear user-friendly error messages if the token has insufficient scopes (e.g. read-only token).
- **[Risk] Terminal Compatibility**: Certain basic terminal emulators may have issues with 24-bit color or mouse support.
  - *Mitigation*: Standardize on Textual's robust terminal capabilities and keyboard navigation shortcuts (`j`/`k`, `Tab`, `1-9`, `Enter`, `Esc`).
