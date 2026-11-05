"""State of a mock interview, independent of any interface."""

from dataclasses import dataclass, field
from enum import Enum

from interview_coach.config import DEFAULT_TURNS, MAX_TURNS, MIN_TURNS


class Role(Enum):
    """Who said a message."""

    TUTOR = "tutor"
    CANDIDATE = "candidate"


@dataclass(frozen=True)
class Message:
    """One line of the conversation."""

    role: Role
    text: str


@dataclass
class InterviewSession:
    """Tracks the messages and turns of one interview."""

    topic: str = ""
    total_turns: int = DEFAULT_TURNS
    messages: list[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the number of turns.

        Raises:
            ValueError: If ``total_turns`` is outside the allowed range.
        """
        if not MIN_TURNS <= self.total_turns <= MAX_TURNS:
            raise ValueError(f"total_turns must be between {MIN_TURNS} and {MAX_TURNS}")

    @property
    def answers_given(self) -> int:
        """Number of answers the candidate has given."""
        return sum(message.role is Role.CANDIDATE for message in self.messages)

    @property
    def current_turn(self) -> int:
        """Number of the turn being answered, starting at 1."""
        return self.answers_given + 1

    @property
    def is_complete(self) -> bool:
        """Whether the candidate has given every answer."""
        return self.answers_given >= self.total_turns

    @property
    def last_question(self) -> str:
        """The tutor's most recent line, or an empty string if there is none."""
        for message in reversed(self.messages):
            if message.role is Role.TUTOR:
                return message.text
        return ""

    def add_question(self, text: str) -> None:
        """Record a line from the tutor.

        Args:
            text: What the tutor said.
        """
        self.messages.append(Message(Role.TUTOR, text))

    def add_answer(self, text: str) -> int:
        """Record an answer from the candidate.

        Args:
            text: What the candidate said.

        Returns:
            The number of the turn this answer belongs to.
        """
        turn = self.current_turn
        self.messages.append(Message(Role.CANDIDATE, text))
        return turn

    def discard_last_answer(self) -> str | None:
        """Remove the last message if it is an answer, so that it can be sent again.

        Returns:
            The text of the removed answer, or ``None`` if the last message is not an answer.
        """
        if self.messages and self.messages[-1].role is Role.CANDIDATE:
            return self.messages.pop().text
        return None
