from __future__ import annotations

import subprocess
from pathlib import Path


class ProjectCommandError(RuntimeError):
    """
    Error raised when a GitHelp project preparation subprocess fails.

    The command output is kept as structured attributes so UI code, tests, or
    future logging can inspect it without parsing the formatted message.
    """

    def __init__(
        self,
        label: str,
        command: list[str],
        stdout: str,
        stderr: str,
    ) -> None:
        self.label = label
        self.command = command
        self.stdout = stdout
        self.stderr = stderr

        super().__init__(
            f"{label}.\n\n"
            f"Command:\n{' '.join(command)}\n\n"
            f"stdout:\n{stdout}\n\n"
            f"stderr:\n{stderr}"
        )


def run_project_command(
    *,
    label: str,
    command: list[str],
    cwd: str | Path,
) -> subprocess.CompletedProcess[str]:
    """
    Run a project preparation command and raise a structured error on failure.
    """
    completed_process = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )

    if completed_process.returncode != 0:
        raise ProjectCommandError(
            label=label,
            command=command,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
        )

    return completed_process
