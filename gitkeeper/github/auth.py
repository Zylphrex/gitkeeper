from typing import Dict, Protocol


class AuthProvider(Protocol):
    """Protocol for providing authentication headers for GitHub API requests."""

    def get_auth_headers(self) -> Dict[str, str]:
        """Return HTTP headers needed for authentication (e.g. Authorization, Accept)."""
        ...


class PersonalAccessTokenProvider:
    """Personal Access Token (PAT) authentication provider."""

    def __init__(self, token: str):
        if not token:
            raise ValueError("Personal Access Token cannot be empty.")
        self.token = token.strip()

    def get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "gitkeeper-cli",
        }
