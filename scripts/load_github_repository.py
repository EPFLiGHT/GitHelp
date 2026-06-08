from __future__ import annotations

import argparse

from githelp.projects.github_loader import load_github_repository
from githelp.utils.paths import PROJECT_ROOT


"""
Clone or reuse a public GitHub repository in GitHelp's local repository folder.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Load a public GitHub repository into GitHelp."
    )

    parser.add_argument(
        "repository_url",
        help="Public GitHub repository URL, for example https://github.com/swiss-ai/mmore.",
    )

    return parser.parse_args()


def main() -> None:
    """Clone or reuse a GitHub repository and print the local path."""
    args = parse_args()

    result = load_github_repository(
        githelp_root=PROJECT_ROOT,
        repository_url=args.repository_url,
    )

    action = "cloned" if result["cloned"] else "reused"

    print(f"Repository {action}: {result['repository_url']}")
    print(f"Project name: {result['project_name']}")
    print(f"Local path: {result['repository_path']}")


if __name__ == "__main__":
    main()
