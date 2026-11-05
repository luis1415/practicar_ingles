import pytest

from interview_coach.config import DEFAULT_TURNS, MAX_TURNS, MIN_TURNS
from interview_coach.interview import InterviewSession


def test_defaults_to_three_turns() -> None:
    assert DEFAULT_TURNS == 3
    assert InterviewSession().total_turns == DEFAULT_TURNS


@pytest.mark.parametrize("turns", [MIN_TURNS - 1, MAX_TURNS + 1])
def test_rejects_turns_out_of_range(turns: int) -> None:
    with pytest.raises(ValueError, match="total_turns"):
        InterviewSession(total_turns=turns)


def test_tracks_turns_until_complete() -> None:
    session = InterviewSession(total_turns=2)
    session.add_question("First?")
    assert session.add_answer("One") == 1
    assert session.current_turn == 2
    assert not session.is_complete
    session.add_question("Second?")
    assert session.last_question == "Second?"
    assert session.add_answer("Two") == 2
    assert session.is_complete


def test_discard_last_answer_only_removes_answers() -> None:
    session = InterviewSession()
    session.add_question("First?")
    assert session.discard_last_answer() is None
    session.add_answer("One")
    assert session.discard_last_answer() == "One"
    assert session.current_turn == 1
