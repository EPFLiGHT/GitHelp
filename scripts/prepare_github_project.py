from __future__ import annotations

import argparse

from githelp.projects.github_loader import prepare_github_project_with_simple_index
from githelp.utils.paths import PROJECT_ROOT


"""
Clone or reuse a public GitHub repository and build a simple GitHelp index.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare a public GitHub repository with GitHelp's simple backend."
    )

    parser.add_argument(
        "repository_url",
        help="Public GitHub repository URL, for example https://github.com/swiss-ai/mmore.",
    )

    parser.add_argument(
        "--project-name",
        default=None,
        help="Optional project name. If omitted, GitHelp infers it from the repository name.",
    )

    return parser.parse_args()


def main() -> None:
    """Clone or reuse a GitHub repository and build its simple index."""
    args = parse_args()

    result = prepare_github_project_with_simple_index(
        githelp_root=PROJECT_ROOT,
        repository_url=args.repository_url,
        project_name=args.project_name,
    )

    action = "cloned" if result["cloned"] else "reused"

    print(f"Repository {action}: {result['repository_url']}")
    print(f"Repository path: {result['repository_path']}")
    print(f"Project name: {result['project_name']}")
    print(f"Project config: {result['project_config_path']}")
    print(f"Corpus path: {result['corpus_path']}")
    print("Backend: simple")

    if result.get("stdout"):
        print()
        print("Corpus build output:")
        print(result["stdout"])

    if result.get("stderr"):
        print()
        print("Corpus build stderr:")
        print(result["stderr"])


if __name__ == "__main__":
    main()
