"""What the AI coach does, independent of any interface."""

from dataclasses import dataclass
from pathlib import Path

from interview_coach import prompts
from interview_coach.config import REPORT_FILE
from interview_coach.interview import InterviewSession
from interview_coach.llm import LLMClient, LLMError
from interview_coach.report import format_transcript, save_report


@dataclass(frozen=True)
class InterviewResult:
    """Outcome of a finished interview."""

    report_path: Path
    advice: str | None


class Coach:
    """Generates questions, corrections and advice using a language model."""

    def __init__(self, llm: LLMClient) -> None:
        """Create the coach.

        Args:
            llm: Client used to reach the language model.
        """
        self._llm = llm

    def next_question(self, session: InterviewSession) -> str:
        """Get the tutor's next line in an interview.

        Args:
            session: The interview so far.

        Returns:
            What the tutor should say.

        Raises:
            LLMError: If the model call fails.
        """
        if session.messages:
            content = f"Conversation so far:\n\n{format_transcript(session.messages)}"
        else:
            content = "The interview is starting. Ask your first question."
        if session.topic:
            content = f"Interview topic or first question: {session.topic}\n\n{content}"
        return self._llm.complete(prompts.INTERVIEWER_PROMPT, content)

    def correct_answer(self, question: str, answer: str) -> str:
        """Get brief corrections for a single answer.

        Args:
            question: The question that was asked.
            answer: The candidate's answer.

        Returns:
            The corrections as plain text.

        Raises:
            LLMError: If the model call fails.
        """
        content = f"Interview question: {question}\n\nAnswer: {answer}"
        return self._llm.complete(prompts.TURN_CORRECTION_PROMPT, content)

    def review_answer(self, transcript: str, question: str | None) -> str:
        """Get full Markdown feedback for one spoken answer.

        Args:
            transcript: Text of the answer.
            question: The question that was answered, if any.

        Returns:
            The feedback in Markdown.

        Raises:
            LLMError: If the model call fails.
        """
        content = f"Transcript of my answer:\n\n{transcript}"
        if question:
            content = f"Interview question: {question}\n\n{content}"
        return self._llm.complete(prompts.FEEDBACK_PROMPT, content)

    def spoken_advice(self, transcript: str, feedback: str) -> str:
        """Get a short recommendation to read aloud.

        Args:
            transcript: Text of the answer or conversation.
            feedback: The written feedback.

        Returns:
            The recommendation in plain English.

        Raises:
            LLMError: If the model call fails.
        """
        content = f"Transcript of my answer:\n\n{transcript}\n\nFeedback:\n\n{feedback}"
        return self._llm.complete(prompts.SPOKEN_ADVICE_PROMPT, content)

    def conclude_interview(
        self, session: InterviewSession, report_path: Path = REPORT_FILE
    ) -> InterviewResult:
        """Save the report of a finished interview and prepare the final advice.

        If the model fails, the conversation is saved anyway with a notice instead of feedback.

        Args:
            session: The finished interview.
            report_path: File where the report is saved.

        Returns:
            The report path and the final advice, if it could be generated.
        """
        transcript = format_transcript(session.messages)
        content = f"Transcript of my answers in a mock interview:\n\n{transcript}"
        try:
            feedback = self._llm.complete(prompts.FEEDBACK_PROMPT, content)
        except LLMError as error:
            feedback = f"No se pudieron generar las correcciones. {error}"
        path = save_report(transcript, feedback, session.topic or None, report_path)

        try:
            advice = self.spoken_advice(transcript, feedback)
        except LLMError:
            advice = None
        return InterviewResult(path, advice)
