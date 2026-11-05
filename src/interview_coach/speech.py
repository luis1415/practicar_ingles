"""Text-to-speech output."""

import shutil
import subprocess
from typing import Protocol

from interview_coach.config import TUTOR_VOICE


class Speaker(Protocol):
    """Anything that can read text aloud; implement it to support another voice engine."""

    def speak(self, text: str) -> bool:
        """Start reading a text aloud without blocking, replacing any current speech.

        Args:
            text: English text to read.

        Returns:
            True if speech started.
        """
        ...

    def stop(self) -> None:
        """Stop any current speech."""
        ...

    def wait(self) -> bool:
        """Block until the current speech finishes.

        Returns:
            True if speech finished successfully.
        """
        ...


class MacSpeaker:
    """Reads text aloud with the macOS ``say`` command."""

    def __init__(self, voice: str = TUTOR_VOICE) -> None:
        """Create the speaker.

        Args:
            voice: Name of an installed macOS voice.
        """
        self._voice = voice
        self._process: subprocess.Popen[bytes] | None = None

    def speak(self, text: str) -> bool:
        """Start reading a text aloud without blocking, replacing any current speech.

        Args:
            text: English text to read.

        Returns:
            True if speech started, False if the ``say`` command is not available.
        """
        self.stop()
        if shutil.which("say") is None:
            return False
        # "--" keeps say from reading the text as options.
        self._process = subprocess.Popen(["say", "-v", self._voice, "--", text])
        return True

    def stop(self) -> None:
        """Stop any current speech."""
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None

    def wait(self) -> bool:
        """Block until the current speech finishes.

        Returns:
            True if speech finished successfully.
        """
        if self._process is None:
            return False
        succeeded = self._process.wait() == 0
        self._process = None
        return succeeded
