"""Local speech-to-text with Whisper."""

from functools import lru_cache

from faster_whisper import WhisperModel

from interview_coach.audio import AudioBuffer
from interview_coach.config import WHISPER_MODEL


@lru_cache(maxsize=1)
def load_whisper_model() -> WhisperModel:
    """Load the Whisper model once, so it can be reused between turns.

    Returns:
        The model, ready to transcribe.
    """
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


def transcribe(audio: AudioBuffer) -> str:
    """Transcribe English speech to text.

    Args:
        audio: Mono float32 audio at ``SAMPLE_RATE`` Hz.

    Returns:
        The full transcript, or an empty string if no speech was detected.
    """
    # Without conditioning or a prompt, Whisper "fixes" less of what you actually said.
    segments, _ = load_whisper_model().transcribe(
        audio, language="en", condition_on_previous_text=False, vad_filter=True
    )
    return " ".join(segment.text.strip() for segment in segments).strip()
