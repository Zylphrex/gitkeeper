## Why

Engineers are overwhelmed by GitHub notification noise, frequently tagged as reviewers on pull requests where they lack context or where action is blocked. `gitkeeper` cuts through this noise to find and prioritize PRs where the user is the right person to review right now, using local git history for fast, zero-API-cost context analysis.

## What Changes

- Introduce a configuration system supporting local repository path mapping, auto-discovery, authentication, and scoring preferences.
- Introduce a GitHub GraphQL client adapter that retrieves pending pull requests, requested reviewers, touched file paths, and CI/review status in minimal network roundtrips.
- Introduce an authentication provider abstraction supporting Personal Access Tokens (PAT) today while remaining forward-compatible with GitHub App installation tokens.
- Introduce a Local Git Context Inspector that inspects local clones and computes time-decayed author touch frequency for modified files.
- Introduce a Relevance & Scoring Engine that gates non-actionable PRs (drafts, failing CI, already reviewed) and computes composite affinity and urgency scores.
- Introduce a terminal-first CLI interface (`gitkeeper queue`) rendering prioritized review queues with clear human-readable explanations.

## Capabilities

### New Capabilities
- `config-management`: Manage user configuration, authentication tokens, repository path mappings, and heuristic scoring preferences.
- `github-client`: Abstract GitHub GraphQL client with authentication provider support for fetching actionable pull requests, touched files, and review states.
- `git-context-inspector`: Analyze local git repositories to determine user commit history, path touch frequency, and time-decayed familiarity with touched files.
- `relevance-scoring`: Evaluate pull requests against actionability filters, assignment types, local git context, and urgency heuristics to compute a composite relevance score.
- `terminal-interface`: Terminal CLI commands and rich table formatting to present prioritized pull request queues with contextual rationales.

### Modified Capabilities
<!-- None: This is the initial capability set for the project. -->

## Impact

- Creates the core architecture and package structure for `gitkeeper`.
- Establishes interfaces for GitHub API interaction, local repository git inspection, scoring pipeline, and CLI commands.
- Adds dependencies for CLI rendering (e.g. `typer` / `rich`), GraphQL HTTP queries (e.g. `httpx`), and YAML configuration parsing (e.g. `pyyaml`).
