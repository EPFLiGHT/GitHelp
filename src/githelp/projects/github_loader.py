from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from githelp.projects.project_builder import ProjectCommandError, slugify_project_name


GITHUB_HTTPS_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
GITHUB_SSH_RE = re.compile(
    r"^git@github\.com:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?$"
)


class GitHubRepositoryReference(TypedDict):
    """Normalized public GitHub repository reference."""

    owner: str
    repo: str
    project_name: str
    clone_url: str


class GitHubRepositoryLoadResult(TypedDict):
    """Local repository result returned after loading a GitHub URL."""

    repository_url: str
    owner: str
    repo: str
    project_name: str
    repository_path: str
    cloned: bool


def parse_github_repository_url(repository_url: str) -> GitHubRepositoryReference:
    """
    Parse and normalize a public GitHub repository URL.

    Supported forms:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git
    """
    repository_url = repository_url.strip()

    if not repository_url:
        raise ValueError("GitHub repository URL is required.")

    match = GITHUB_HTTPS_RE.match(repository_url) or GITHUB_SSH_RE.match(repository_url)

    if not match:
        parsed_url = urlparse(repository_url)
        host = parsed_url.netloc or "unknown host"
        raise ValueError(
            "Unsupported GitHub repository URL. Expected a public GitHub URL "
            f"such as https://github.com/owner/repo, got host: {host}."
        )

    owner = match.group("owner")
    repo = match.group("repo")
    project_name = slugify_project_name(repo)

    return {
        "owner": owner,
        "repo": repo,
        "project_name": project_name,
        "clone_url": f"https://github.com/{owner}/{repo}.git",
    }


def get_github_repository_path(
    githelp_root: str | Path,
    reference: GitHubRepositoryReference,
) -> Path:
    """
    Return the local GitHelp-managed path for a GitHub repository.
    """
    githelp_root = Path(githelp_root).resolve()
    folder_name = slugify_project_name(f"{reference['owner']}-{reference['repo']}")

    return githelp_root / "data" / "repositories" / folder_name


def load_github_repository(
    githelp_root: str | Path,
    repository_url: str,
) -> GitHubRepositoryLoadResult:
    """
    Clone a public GitHub repository into GitHelp's local repository folder.

    If the repository folder already exists and contains files, GitHelp reuses
    it instead of overwriting local state.
    """
    reference = parse_github_repository_url(repository_url)
    repository_path = get_github_repository_path(githelp_root, reference)

    if repository_path.exists() and any(repository_path.iterdir()):
        return {
            "repository_url": reference["clone_url"],
            "owner": reference["owner"],
            "repo": reference["repo"],
            "project_name": reference["project_name"],
            "repository_path": str(repository_path),
            "cloned": False,
        }

    repository_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        reference["clone_url"],
        str(repository_path),
    ]

    completed_process = subprocess.run(
        command,
        text=True,
        capture_output=True,
    )

    if completed_process.returncode != 0:
        raise ProjectCommandError(
            label="GitHub repository clone failed",
            command=command,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
        )

    return {
        "repository_url": reference["clone_url"],
        "owner": reference["owner"],
        "repo": reference["repo"],
        "project_name": reference["project_name"],
        "repository_path": str(repository_path),
        "cloned": True,
    }
