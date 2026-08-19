import logging
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
  hot_window_hours: 12
  min_affinity_files: 2
"""
    )

    cfg = load_config(config_file)
    assert cfg.github.token == "ghp_secret123"
    assert cfg.github.user == "octocat"
    assert cfg.heuristics.lookback_days == 90
    assert cfg.heuristics.hot_window_hours == 12
    assert cfg.heuristics.min_affinity_files == 2


def test_deprecated_min_score_threshold_warns(monkeypatch, tmp_path, caplog):
    monkeypatch.setenv("TEST_GH_TOKEN", "ghp_secret123")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
heuristics:
  min_score_threshold: 40
"""
    )
    with caplog.at_level(logging.WARNING, logger="gitkeeper.config"):
        cfg = load_config(config_file)
    assert "min_score_threshold" in caplog.text
    assert not hasattr(cfg.heuristics, "min_score_threshold")


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


def test_followup_config_defaults():
    from gitkeeper.config import Config

    cfg = Config()
    assert cfg.followup.include_authored is True
    assert cfg.followup.show_waiting_on_author is True
    assert cfg.followup.show_waiting_on_others is True
    assert cfg.followup.staleness_warn_after_days == 3


def test_load_config_parses_followup_block(monkeypatch, tmp_path):
    from gitkeeper.config import Config

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
followup:
  include_authored: false
  show_waiting_on_author: false
  staleness_warn_after_days: 7
"""
    )
    cfg = load_config(config_file)
    assert isinstance(cfg.followup, Config.model_fields["followup"].annotation)
    assert cfg.followup.include_authored is False
    assert cfg.followup.show_waiting_on_author is False
    assert cfg.followup.show_waiting_on_others is True
    assert cfg.followup.staleness_warn_after_days == 7
