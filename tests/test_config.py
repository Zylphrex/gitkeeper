import os
import tempfile
from pathlib import Path
import pytest
from gitkeeper.config import load_config
from gitkeeper.repos import RepoLocator, extract_github_repo_slug


def test_extract_github_repo_slug():
    assert extract_github_repo_slug("git@github.com:foo/bar.git") == "foo/bar"
    assert extract_github_repo_slug("https://github.com/foo/bar.git") == "foo/bar"
    assert extract_github_repo_slug("https://github.com/foo/bar") == "foo/bar"
    assert extract_github_repo_slug("https://gitlab.com/foo/bar.git") is None


def test_load_config_with_env_expansion(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_GH_TOKEN", "ghp_secret123")
    monkeypatch.setenv("TEST_GH_USER", "octocat")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
github:
  token: "${TEST_GH_TOKEN}"
  user: "$TEST_GH_USER"
heuristics:
  lookback_days: 90
  min_score_threshold: 50
"""
    )

    cfg = load_config(config_file)
    assert cfg.github.token == "ghp_secret123"
    assert cfg.github.user == "octocat"
    assert cfg.heuristics.lookback_days == 90
    assert cfg.heuristics.min_score_threshold == 50


def test_repo_locator_explicit_mapping(tmp_path):
    repo_dir = tmp_path / "my-repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    cfg = load_config(tmp_path / "missing.yaml")
    cfg.repositories.mapping["myorg/my-repo"] = str(repo_dir)

    locator = RepoLocator(cfg.repositories)
    resolved = locator.resolve("myorg/my-repo")
    assert resolved == repo_dir.resolve()
    assert locator.resolve("myorg/unknown") is None
