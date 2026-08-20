# gitkeeper

Cuts through GitHub notification noise to find the pull requests you're the right person to review.

![gitkeeper demo](demos/gitkeeper-demo.gif)

> Fullscreen MP4 version: [`demos/gitkeeper-demo.mp4`](demos/gitkeeper-demo.mp4) · Tapes in [`demos/`](demos/)

## What it does

Gitkeeper pulls every open pull request that involves you — review requests, your own PRs, and PRs you've already reviewed — filters out anything that isn't actionable (drafts, closed PRs, failing CI), then asks one question per PR:

> **Whose move is it?**

Each entry shows its turn state at a glance:

| Glyph | Meaning                                                                                         |
| ----- | ----------------------------------------------------------------------------------------------- |
| `●`   | **Your move** — review is due, or a re-review because the author pushed after your last verdict |
| `○`   | **Waiting on others** — reviewers, CI, or merge                                                 |
| `◇`   | **Waiting on author** — you asked for changes and no new commits have landed                    |

Queue order is purely by most recent activity — the noisy ones float to the top, nothing is silently hidden behind an arbitrary score.

For PRs where it's your move, gitkeeper explains _why_: "you're the bottleneck", "directly requested", "re-review due", "respond to review" — and, when it can find a local clone of the repo, chips in "touched N/M files" based on your authorship and recent commit history.

Select a PR and you get a split-screen review surface: the full diff, existing review threads anchored to their lines, and inline comment boxes — everything you need to review without leaving the terminal.

## Install

Requires **Python ≥ 3.10**.

With [uv](https://docs.astral.sh/uv/):

```
uv sync
```

or with plain pip, from a checkout:

```
python -m pip install -e .
```

## Configure

Gitkeeper needs a GitHub personal access token. Set it in the environment, or in a config file.

```
export GITHUB_TOKEN=ghp_...
export GITHUB_USER=yourname   # optional; auto-detected if omitted
```

Or create a config file (Gitkeeper checks `.gitkeeper.yaml` / `.gitkeeper.yml` in the working directory, then `~/.config/gitkeeper/config.yaml`):

```yaml
github:
  token: ${GITHUB_TOKEN}
  user: yourname

repositories:
  auto_discover_dir: ~/repos # find local clones by origin URL
  mapping: # or map explicitly owner/repo → path
    yourorg/something: /path/to/something

git:
  author_emails:
    - you@example.com
  author_names:
    - Your Name

heuristics:
  lookback_days: 180 # git-history window for touch context
  ignore_drafts: true
  ignore_failing_ci: true
  ignored_paths: ["*.lock", "docs/**", "migrations/**"]

followup:
  include_authored: true # include your open authored PRs
  include_reviewed: true # include PRs you've already reviewed

cli:
  max_items: 10
```

Environment variables in config values are expanded (`${VAR}` or `$VAR`).

## Usage

```
gitkeeper
```

`h` / `l` moves focus between the PR list and the diff pane; `tab` toggles focus as well.

## Keybindings

| Key                 | Action                                                      |
| ------------------- | ----------------------------------------------------------- |
| `j` / `k`           | Move up / down                                              |
| `h` / `l`           | Move focus left (PR list) / right (diff pane)               |
| `gg` / `G`          | Jump to top / bottom                                        |
| `Ctrl+d` / `Ctrl+u` | Page down / up                                              |
| `/`                 | Search the focused zone (PRs, files, or diff lines)         |
| `n` / `N`           | Next / previous search match                                |
| `o`                 | Open the selected PR in your browser                        |
| `c`                 | Add an inline comment on the selected diff line (diff pane) |
| `s`                 | Submit a review (diff pane)                                 |
| `w`                 | Toggle whitespace-only changes (diff pane)                  |
| `r`                 | Refresh the queue                                           |
| `q`                 | Quit                                                        |

`c`, `s`, and `w` are scoped to the diff pane and appear in the footer only when your focus is there.

## Demo

Recorded against a mock GitHub client — that's real app code, fake data:

```
.venv/bin/python demos/demo_gitkeeper.py
```

## License

[MIT](LICENSE)
