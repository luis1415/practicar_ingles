"""Microphone recording."""

import sys

import numpy as np
import numpy.typing as npt
import sounddevice as sd

from interview_coach.config import MIN_RECORDING_SECONDS, SAMPLE_RATE

AudioBuffer = npt.NDArray[np.float32]


def is_too_short(audio: AudioBuffer) -> bool:
    """Tell whether a recording is too short to contain an answer.

    Args:
        audio: Mono audio at ``SAMPLE_RATE`` Hz.

    Returns:
        True if the recording lasts less than ``MIN_RECORDING_SECONDS``.
    """
    return len(audio) < SAMPLE_RATE * MIN_RECORDING_SECONDS


class Recorder:
    """Records from the microphone between calls to ``start`` and ``stop``."""

    def __init__(self) -> None:
        """Create the recorder without opening the microphone."""
        self._blocks: list[AudioBuffer] = []
        self._stream: sd.InputStream | None = None

    def _on_audio(
        self,
        indata: AudioBuffer,
        frames: int,
        time: object,  # CFFI struct with timestamps; unused
        status: sd.CallbackFlags,
    ) -> None:
        """Collect each audio block delivered by sounddevice."""
        if status:
            print(status, file=sys.stderr)
        self._blocks.append(indata.copy())

    def start(self) -> None:
        """Open the microphone and start collecting audio."""
        self._blocks = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=self._on_audio
        )
        self._stream.start()

    def stop(self) -> AudioBuffer:
        """Close the microphone and return what was recorded.

        Returns:
            Mono float32 audio at ``SAMPLE_RATE`` Hz. Empty if nothing was captured.
        """
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._blocks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._blocks).flatten()
