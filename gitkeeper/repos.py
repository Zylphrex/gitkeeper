import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from gitkeeper.config import RepositoriesConfig


def extract_github_repo_slug(remote_url: str) -> Optional[str]:
    """
    Extract 'owner/repo' from a git remote URL.
    Supports SSH (git@github.com:owner/repo.git) and HTTPS (https://github.com/owner/repo.git).
    """
    remote_url = remote_url.strip()
    match = re.search(r"github\.com[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?$", remote_url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return f"{owner}/{repo}".lower()
    return None


def get_git_remote_url(repo_path: Path) -> Optional[str]:
    """Get the origin remote URL for a local git directory."""
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


class RepoLocator:
    def __init__(self, config: RepositoriesConfig):
        self.config = config
        self._cache: Dict[str, Optional[Path]] = {}
        self._scanned = False
        self._discovered: Dict[str, Path] = {}

    def _scan_auto_discover_dir(self) -> None:
        if self._scanned:
            return
        self._scanned = True

        if not self.config.auto_discover_dir:
            return

        base_dir = Path(self.config.auto_discover_dir).expanduser().resolve()
        if not base_dir.is_dir():
            return

        # Scan depth 1 and 2 directories for .git
        for child in base_dir.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                if (child / ".git").exists():
                    url = get_git_remote_url(child)
                    if url:
                        slug = extract_github_repo_slug(url)
                        if slug and slug not in self._discovered:
                            self._discovered[slug] = child
                else:
                    # Scan depth 2 (e.g. ~/repos/org/repo)
                    try:
                        for subchild in child.iterdir():
                            if subchild.is_dir() and (subchild / ".git").exists():
                                url = get_git_remote_url(subchild)
                                if url:
                                    slug = extract_github_repo_slug(url)
                                    if slug and slug not in self._discovered:
                                        self._discovered[slug] = subchild
                    except PermissionError:
                        continue

    def resolve(self, repo_slug: str) -> Optional[Path]:
        """Resolve a GitHub 'owner/repo' slug to a local repository Path."""
        norm_slug = repo_slug.strip().lower()
        if norm_slug in self._cache:
            return self._cache[norm_slug]

        # 1. Check explicit mappings
        for map_slug, raw_path in self.config.mapping.items():
            if map_slug.strip().lower() == norm_slug:
                p = Path(raw_path).expanduser().resolve()
                if p.is_dir() and (p / ".git").exists():
                    self._cache[norm_slug] = p
                    return p

        # 2. Check auto-discover directory
        self._scan_auto_discover_dir()
        if norm_slug in self._discovered:
            p = self._discovered[norm_slug]
            self._cache[norm_slug] = p
            return p

        self._cache[norm_slug] = None
        return None
