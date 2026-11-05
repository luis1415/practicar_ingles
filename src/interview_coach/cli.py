"""Terminal interface: answer one question and get feedback.

Records your answer from the microphone, transcribes it locally with Whisper and asks the
coach for corrections. The result is saved to resultados/ultima_practica.md, which is replaced
on every run. At the end, a short recommendation is read aloud in English.

Usage:
    uv run practice
    uv run practice --question "Tell me about yourself"
"""

import argparse
import sys

from interview_coach.audio import AudioBuffer, Recorder, is_too_short
from interview_coach.coach import Coach
from interview_coach.config import TUTOR_VOICE, WHISPER_MODEL
from interview_coach.llm import ClaudeCliClient, LLMError
from interview_coach.report import save_report
from interview_coach.speech import MacSpeaker
from interview_coach.transcription import transcribe


def record_answer() -> AudioBuffer:
    """Record from the microphone until the user presses Enter.

    Returns:
        Mono float32 audio. Empty if nothing was captured.
    """
    recorder = Recorder()
    input("Press Enter to start recording...")
    recorder.start()
    input("Recording... speak in English and press Enter to finish.")
    return recorder.stop()


def read_advice_aloud(coach: Coach, transcript: str, feedback: str) -> None:
    """Read a short tutor recommendation aloud; failures only print a warning.

    Args:
        coach: Coach that writes the recommendation.
        transcript: Text of the spoken answer.
        feedback: The written feedback.
    """
    print("\nPreparing your tutor's advice...")
    try:
        advice = coach.spoken_advice(transcript, feedback)
    except LLMError as error:
        print(f"Could not generate the spoken advice. {error}", file=sys.stderr)
        return

    print(f"\nYour tutor says:\n{advice}")
    speaker = MacSpeaker()
    if not speaker.speak(advice) or not speaker.wait():
        print(f"Could not read the advice with the voice {TUTOR_VOICE}.", file=sys.stderr)


def main() -> None:
    """Run the full flow: record, transcribe, correct, save and read the advice."""
    parser = argparse.ArgumentParser(description="Practice job interviews in English.")
    parser.add_argument("--question", "-q", help="Interview question you are going to answer")
    args = parser.parse_args()

    if args.question:
        print(f"\nQuestion: {args.question}\n")

    audio = record_answer()
    if is_too_short(audio):
        sys.exit("The recording is too short.")

    print(f"Transcribing with Whisper ({WHISPER_MODEL})...")
    transcript = transcribe(audio)
    if not transcript:
        sys.exit("No speech detected. Check your terminal's microphone permission.")
    print(f"\nWhat you said:\n{transcript}\n")

    coach = Coach(ClaudeCliClient())
    print("Asking Claude for corrections...")
    try:
        feedback = coach.review_answer(transcript, args.question)
    except LLMError as error:
        sys.exit(str(error))
    print(feedback)

    report = save_report(transcript, feedback, args.question)
    print(f"\nSaved to {report}")

    read_advice_aloud(coach, transcript, feedback)


if __name__ == "__main__":
    main()
