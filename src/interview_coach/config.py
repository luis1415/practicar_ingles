"""Application settings shared by the terminal and desktop interfaces."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_RATE = 16_000  # Whisper works at 16 kHz
MIN_RECORDING_SECONDS = 1
WHISPER_MODEL = "small.en"  # "base.en" is faster, "medium.en" is more accurate
TUTOR_VOICE = "Samantha (Mejorada)"  # macOS English voice; list them with: say -v '?'
REPORT_FILE = PROJECT_ROOT / "resultados" / "ultima_practica.md"

DEFAULT_TURNS = 3
MIN_TURNS = 1
MAX_TURNS = 10
