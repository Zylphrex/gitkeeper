import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import yaml


class GitHubConfig(BaseModel):
    token: Optional[str] = Field(default=None, description="Personal access token or App token")
    user: Optional[str] = Field(default=None, description="GitHub username")


class RepositoriesConfig(BaseModel):
    auto_discover_dir: Optional[str] = Field(
        default=None, description="Root directory to auto-discover cloned git repositories"
    )
    mapping: Dict[str, str] = Field(
        default_factory=dict, description="Explicit owner/repo to local directory mapping"
    )


class HeuristicsConfig(BaseModel):
    lookback_days: int = Field(default=180, description="Git history lookback in days")
    min_score_threshold: int = Field(
        default=40, description="Minimum score to show in primary queue"
    )
    ignore_drafts: bool = Field(default=True, description="Filter out draft PRs")
    ignore_failing_ci: bool = Field(default=True, description="Filter out failing CI PRs")
    ignored_paths: List[str] = Field(
        default_factory=lambda: ["*.lock", "docs/**", "migrations/**"],
        description="Path patterns to ignore during context matching",
    )


class GitConfig(BaseModel):
    author_emails: List[str] = Field(
        default_factory=list, description="Author emails to match in git commit logs"
    )
    author_names: List[str] = Field(
        default_factory=list, description="Author names to match in git commit logs"
    )


class CLIConfig(BaseModel):
    default_view: str = Field(default="queue", description="Default view mode")
    max_items: int = Field(default=10, description="Max items to display")


class Config(BaseModel):
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    repositories: RepositoriesConfig = Field(default_factory=RepositoriesConfig)
    heuristics: HeuristicsConfig = Field(default_factory=HeuristicsConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)


def _expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables like ${VAR} or $VAR in strings."""
    if isinstance(value, str):
        # Match ${VAR} or $VAR
        pattern = re.compile(r"\$(?:\{([A-Za-z0-9_]+)\}|([A-Za-z0-9_]+))")

        def replace(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, "")

        return pattern.sub(replace, value)
    elif isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from the specified path or default locations."""
    paths_to_check = []
    if config_path:
        paths_to_check.append(Path(config_path))
    else:
        # Check current working directory .gitkeeper.yaml
        paths_to_check.append(Path.cwd() / ".gitkeeper.yaml")
        paths_to_check.append(Path.cwd() / ".gitkeeper.yml")
        # Check user config directory ~/.config/gitkeeper/config.yaml
        user_config_dir = Path.home() / ".config" / "gitkeeper"
        paths_to_check.append(user_config_dir / "config.yaml")
        paths_to_check.append(user_config_dir / "config.yml")

    raw_data: Dict[str, Any] = {}
    for p in paths_to_check:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if isinstance(loaded, dict):
                        raw_data = loaded
                        break
            except Exception:
                pass

    expanded_data = _expand_env_vars(raw_data)
    config = Config.model_validate(expanded_data)

    # Fallback to GITHUB_TOKEN / GITHUB_USER if not set in config
    if not config.github.token:
        config.github.token = os.environ.get("GITHUB_TOKEN")
    if not config.github.user:
        config.github.user = os.environ.get("GITHUB_USER")

    return config
