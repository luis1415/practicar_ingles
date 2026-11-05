"""Markdown report of a practice session.

The report is written for a Spanish-speaking learner, so its labels stay in Spanish.
"""

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from interview_coach.config import REPORT_FILE
from interview_coach.interview import Message, Role

ROLE_LABELS = {Role.TUTOR: "Tutor", Role.CANDIDATE: "Yo"}


def format_transcript(messages: Iterable[Message]) -> str:
    """Convert messages into Markdown text.

    Args:
        messages: Messages in order.

    Returns:
        The conversation, with one paragraph per message.
    """
    return "\n\n".join(f"**{ROLE_LABELS[m.role]}:** {m.text}" for m in messages)


def save_report(
    transcript: str, feedback: str, question: str | None, path: Path = REPORT_FILE
) -> Path:
    """Save a practice session, replacing the previous one.

    Args:
        transcript: What the candidate said.
        feedback: Feedback from the coach.
        question: Interview question or topic, if any.
        path: File to write.

    Returns:
        The path of the saved file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# Practica {datetime.now():%Y-%m-%d %H:%M}\n"]
    if question:
        parts.append(f"**Pregunta:** {question}\n")
    parts.append(f"## Lo que dije\n\n{transcript}\n")
    parts.append(f"## Correcciones\n\n{feedback}\n")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
