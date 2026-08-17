## Context

See `proposal.md` for background and problem statement.

`gitkeeper` is a greenfield Python-based CLI tool. It operates by combining remote GitHub pull request metadata (fetched via GraphQL) with local git repository inspection to rank review requests by context, actionability, and urgency.

## Goals / Non-Goals

**Goals:**
- Provide a clean modular Python package architecture (`gitkeeper`).
- Implement GitHub GraphQL client with pluggable authentication (PAT supported first, GitHub App JWT ready).
- Inspect local git repositories with `git log` to calculate decay-weighted author commit counts on touched files without API overhead.
- Implement a composite scoring pipeline producing 0–100 scores with human-readable rationales.
- Deliver an intuitive, fast CLI command (`gitkeeper queue`) using `typer` and `rich`.

**Non-Goals:**
- Building a full background daemon or web server in this change.
- Automated PR re-assignment or posting comments to GitHub in this phase.
- Supporting non-GitHub VCS providers (e.g. GitLab, Bitbucket).

## Decisions

### 1. GitHub API: GraphQL over REST
- **Decision**: Use GitHub's GraphQL API as the primary data retrieval mechanism.
- **Rationale**: Fetching pending review requests along with file paths, commit counts, review states, and check suites takes a single round-trip query in GraphQL. Doing this in REST requires $1 + 3N$ requests (search + PR details + files + reviews).
- **Alternative Considered**: GitHub REST API — discarded due to N+1 rate-limiting and latency constraints for users with many open review requests.

### 2. Authentication Abstraction
- **Decision**: Define an `AuthProvider` protocol/interface with `PersonalAccessTokenProvider` as the initial implementation.
- **Rationale**: Keeps all HTTP headers and token management decoupled from GraphQL client logic, making future GitHub App installation token generation drop-in compatible.
- **Alternative Considered**: Hardcoding PAT bearer token headers directly in the GraphQL client.

### 3. Local Git Inspection Strategy
- **Decision**: Use `subprocess` or `git` CLI wrappers to run targeted `git log --author=<user> --since=<date> -- <paths>` commands against resolved local clones.
- **Rationale**: Executing native git against local clones is nearly instantaneous (milliseconds) and requires no remote network calls or token permissions.
- **Alternative Considered**: Fetching commit blame/history via GitHub REST/GraphQL API — discarded due to severe API rate limits and slower execution.

### 4. Scoring Formulation & Breakdown
- **Decision**: Score PRs on a 0–100 scale using a composite of:
  - **Actionability Gate**: Multiplier 0 for drafts, already reviewed PRs, or blocked states.
  - **Affinity (0–50 pts)**: Proportion of files touched where user has authored commits in last 90d (+10/file) and 90-180d (+5/file).
  - **Assignment (0–35 pts)**: Direct review request (+30), mention (+20), team alias (+10).
  - **Urgency & Size (0–15 pts)**: Diff under 100 lines (+10), waiting > 24 hours (+5).
- **Rationale**: Provides clear differentiation between broadcast noise (10 pts) and high-context direct reviews (85+ pts) while rewarding fast turnarounds on small PRs.

### 5. CLI Framework: Typer + Rich
- **Decision**: Use `typer` for CLI argument parsing and `rich` for terminal table formatting and status spinners.
- **Rationale**: Python standard for modern CLI development, provides beautiful colored tables, and simplifies command extensions.

## Risks / Trade-offs

- **[Risk] Missing Local Repository Clones**: The user may not have every repository cloned locally.
  - **Mitigation**: Gracefully degrade affinity scoring for missing repos (flag as "No local clone found") and rely on assignment/urgency weights rather than failing the command.
- **[Risk] Large File Lists on Giant PRs**: A PR modifying 500+ files could slow down git log querying.
  - **Mitigation**: Chunk or cap path inspections (e.g., sample top 50 files or root directories) and truncate gracefully.
- **[Risk] Git Author Email / Name Mismatch**: The user's GitHub username may not match their local git commit author name/email.
  - **Mitigation**: Support `git.author_emails` and `git.author_names` in `config.yaml` to match local commit signatures accurately.
