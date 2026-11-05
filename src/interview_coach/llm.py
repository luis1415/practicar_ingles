"""Access to the language model behind the coach."""

import shutil
import subprocess
import tempfile
from typing import Protocol


class LLMError(RuntimeError):
    """The language model could not produce a reply."""


class LLMClient(Protocol):
    """Anything that can answer a message; implement it to support another provider."""

    def complete(self, system_prompt: str, content: str) -> str:
        """Get a reply from the model.

        Args:
            system_prompt: System instructions for the model.
            content: The user message.

        Returns:
            The reply as text.

        Raises:
            LLMError: If no reply could be obtained.
        """
        ...


class ClaudeCliClient:
    """Calls Claude through the Claude Code CLI, using the user's subscription."""

    def complete(self, system_prompt: str, content: str) -> str:
        """Get a reply from Claude.

        Args:
            system_prompt: System instructions for Claude.
            content: The message Claude receives through stdin.

        Returns:
            The reply as text.

        Raises:
            LLMError: If the ``claude`` CLI is not installed or the call fails.
        """
        if shutil.which("claude") is None:
            raise LLMError("The 'claude' command was not found. Install Claude Code and log in.")

        # No tools, no saved session and no project settings: just a text reply to our prompt.
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--system-prompt",
                system_prompt,
                "--tools",
                "",
                "--no-session-persistence",
                "--setting-sources",
                "",
            ],
            input=content,
            capture_output=True,
            text=True,
            cwd=tempfile.gettempdir(),
            check=False,
        )
        if result.returncode != 0:
            raise LLMError(f"The call to Claude failed:\n{result.stderr or result.stdout}")
        return result.stdout.strip()
