## 1. Project Setup and Configuration Management

- [x] 1.1 Configure Python project dependencies (e.g. `typer`, `rich`, `httpx`, `pyyaml`, `pydantic`) in `pyproject.toml`
- [x] 1.2 Implement configuration data models and YAML parser with environment variable interpolation in `gitkeeper/config.py`
- [x] 1.3 Implement repository locator and directory auto-discovery in `gitkeeper/repos.py`
- [x] 1.4 Add unit tests for configuration loading and repo path resolution in `tests/test_config.py`

## 2. GitHub Client and Authentication Provider

- [x] 2.1 Define `AuthProvider` interface and implement `PersonalAccessTokenProvider` in `gitkeeper/github/auth.py`
- [x] 2.2 Construct GraphQL queries for review requests, PR files, check suites, and review states in `gitkeeper/github/queries.py`
- [x] 2.3 Implement `GitHubGraphQLClient` to execute batch PR fetching with error handling in `gitkeeper/github/client.py`
- [x] 2.4 Add unit and mock tests for GitHub client and auth provider in `tests/test_github_client.py`

## 3. Local Git Context Inspector

- [x] 3.1 Implement local git inspection functions using `git log` to query author commit history for file paths in `gitkeeper/git/inspector.py`
- [x] 3.2 Implement decay-weighted path touch scoring (e.g. <90 days vs 90-180 days) in `gitkeeper/git/decay.py`
- [x] 3.3 Handle missing clones and edge cases gracefully with neutral fallbacks
- [x] 3.4 Add unit tests for local git inspector with temporary git repositories in `tests/test_git_inspector.py`

## 4. Relevance Scoring and Gating Engine

- [x] 4.1 Implement actionability filter gates (drafts, already approved, failing CI) in `gitkeeper/scoring/gates.py`
- [x] 4.2 Implement scoring heuristics (affinity points, assignment points, size/urgency modifiers) in `gitkeeper/scoring/calculator.py`
- [x] 4.3 Combine gating and scoring into a unified ranking pipeline in `gitkeeper/scoring/pipeline.py`
- [x] 4.4 Add unit tests for scoring and gating combinations in `tests/test_scoring.py`

## 5. Terminal CLI Interface

- [x] 5.1 Create Typer CLI app entrypoint with `queue` / `list` commands in `gitkeeper/cli.py`
- [x] 5.2 Implement Rich table formatting with score, PR link, author, title, and rationale in `gitkeeper/ui/table.py`
- [x] 5.3 Implement filtering options (`--all`, `--threshold`, `--json`)
- [x] 5.4 Add CLI integration tests using Typer's `CliRunner` in `tests/test_cli.py`
