from pathlib import Path

from interview_coach import prompts
from interview_coach.coach import Coach
from interview_coach.interview import InterviewSession
from interview_coach.llm import LLMError


class FakeLLM:
    def __init__(self, failing_prompts: tuple[str, ...] = ()) -> None:
        self.failing_prompts = failing_prompts
        self.contents: list[str] = []

    def complete(self, system_prompt: str, content: str) -> str:
        if system_prompt in self.failing_prompts:
            raise LLMError("model down")
        self.contents.append(content)
        return "reply"


def finished_session() -> InterviewSession:
    session = InterviewSession(topic="kubernetes", total_turns=1)
    session.add_question("Tell me about pods.")
    session.add_answer("I am work with pods.")
    return session


def test_next_question_sends_topic_and_conversation() -> None:
    llm = FakeLLM()
    Coach(llm).next_question(finished_session())
    assert "kubernetes" in llm.contents[0]
    assert "I am work with pods." in llm.contents[0]


def test_conclude_saves_report_with_transcript(tmp_path: Path) -> None:
    result = Coach(FakeLLM()).conclude_interview(finished_session(), tmp_path / "out" / "r.md")
    text = result.report_path.read_text(encoding="utf-8")
    assert result.advice == "reply"
    assert "**Pregunta:** kubernetes" in text
    assert "**Yo:** I am work with pods." in text


def test_conclude_keeps_conversation_when_model_fails(tmp_path: Path) -> None:
    llm = FakeLLM((prompts.FEEDBACK_PROMPT, prompts.SPOKEN_ADVICE_PROMPT))
    result = Coach(llm).conclude_interview(finished_session(), tmp_path / "r.md")
    text = result.report_path.read_text(encoding="utf-8")
    assert result.advice is None
    assert "**Yo:** I am work with pods." in text
    assert "model down" in text
