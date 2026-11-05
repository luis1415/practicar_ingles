"""Desktop interface: a short mock interview with an AI tutor.

The tutor interviews you in English and reads each question aloud. You answer by speaking or
typing. The corrections of each answer appear as text without interrupting the interview, and
at the end the report is saved to resultados/ultima_practica.md.

Usage:
    uv run tutor
"""

import subprocess
import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path

import customtkinter as ctk

from interview_coach.audio import AudioBuffer, Recorder, is_too_short
from interview_coach.coach import Coach, InterviewResult
from interview_coach.config import MAX_TURNS, MIN_TURNS, REPORT_FILE
from interview_coach.gui import theme
from interview_coach.gui.widgets import ChatView, Composer, CorrectionsView, TurnStepper
from interview_coach.gui.worker import BackgroundTasks
from interview_coach.interview import InterviewSession
from interview_coach.llm import ClaudeCliClient
from interview_coach.speech import MacSpeaker, Speaker
from interview_coach.transcription import transcribe

POLL_INTERVAL_MS = 100
TUTOR_NAME = "Tutor"
CANDIDATE_NAME = "You"


class TutorApp:
    """Connects the window with the interview: it reacts to events and shows the results."""

    def __init__(
        self,
        root: ctk.CTk,
        coach: Coach,
        speaker: Speaker,
        recorder: Recorder,
        transcriber: Callable[[AudioBuffer], str] = transcribe,
        report_path: Path = REPORT_FILE,
    ) -> None:
        """Build the window and start waiting for results from background tasks.

        Args:
            root: Main window.
            coach: Generates questions, corrections and advice.
            speaker: Reads the tutor's lines aloud.
            recorder: Records the user's answers.
            transcriber: Converts recorded audio into text.
            report_path: File where the report is saved.
        """
        self._root = root
        self._coach = coach
        self._speaker = speaker
        self._recorder = recorder
        self._transcriber = transcriber
        self._report_path = report_path
        self._tasks = BackgroundTasks()
        self._session: InterviewSession | None = None
        self._saved_report: Path | None = None
        self._recording = False

        self._build_window()
        self._composer.set_mode("locked")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._poll_tasks()

    def _build_window(self) -> None:
        """Create the layout of the window."""
        self._root.title("Interview Tutor")
        self._root.geometry("1080x700")
        self._root.minsize(860, 560)
        self._root.configure(fg_color=theme.BACKGROUND)
        self._root.columnconfigure(1, weight=3)
        self._root.columnconfigure(2, weight=2)
        self._root.rowconfigure(0, weight=1)

        self._build_sidebar()

        conversation = ctk.CTkFrame(self._root, fg_color="transparent")
        conversation.grid(row=0, column=1, sticky="nsew", padx=theme.GAP, pady=theme.GAP)
        conversation.columnconfigure(0, weight=1)
        conversation.rowconfigure(1, weight=1)
        self._section_title(conversation, "Conversation").grid(row=0, column=0, sticky="w")
        self._chat = ChatView(conversation, "Choose your turns and press Start interview.")
        self._chat.grid(row=1, column=0, sticky="nsew", pady=(theme.SMALL_GAP, theme.SMALL_GAP))
        self._status = ctk.CTkLabel(
            conversation,
            text="Ready when you are.",
            text_color=theme.MUTED,
            font=theme.font(13),
            anchor="w",
            justify="left",
        )
        self._status.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        conversation.bind("<Configure>", self._on_conversation_resize)
        self._composer = Composer(conversation, self.send_text, self.toggle_recording)
        self._composer.grid(row=3, column=0, sticky="ew")
        ctk.CTkLabel(
            conversation,
            text="Enter sends · Shift+Enter adds a new line",
            text_color=theme.MUTED,
            font=theme.font(11),
        ).grid(row=4, column=0, sticky="e", pady=(4, 0))

        corrections = ctk.CTkFrame(self._root, fg_color="transparent")
        corrections.grid(row=0, column=2, sticky="nsew", padx=(0, theme.GAP), pady=theme.GAP)
        corrections.columnconfigure(0, weight=1)
        corrections.rowconfigure(1, weight=1)
        self._section_title(corrections, "Corrections").grid(row=0, column=0, sticky="w")
        self._corrections = CorrectionsView(
            corrections, "Corrections for each answer appear here while the interview continues."
        )
        self._corrections.grid(row=1, column=0, sticky="nsew", pady=(theme.SMALL_GAP, 0))

    def _on_conversation_resize(self, event: "tk.Event[tk.Misc]") -> None:
        """Keep the status text within the width of the conversation.

        Args:
            event: Tkinter resize event.
        """
        self._status.configure(wraplength=int(event.width / self._status._get_widget_scaling()))

    def _build_sidebar(self) -> None:
        """Create the panel where the interview is set up."""
        sidebar = ctk.CTkFrame(self._root, width=260, fg_color=theme.SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.pack_propagate(False)
        padding = {"padx": 20, "fill": "x"}

        ctk.CTkLabel(
            sidebar,
            text="Interview Tutor",
            text_color=theme.TEXT,
            font=theme.font(22, bold=True),
            anchor="w",
        ).pack(pady=(24, 0), **padding)
        ctk.CTkLabel(
            sidebar,
            text="Practice speaking English for your next interview.",
            text_color=theme.MUTED,
            font=theme.font(13),
            anchor="w",
            justify="left",
            wraplength=220,
        ).pack(pady=(4, 24), **padding)

        self._field_title(sidebar, "Topic or question (optional)").pack(pady=(0, 6), **padding)
        self._topic = ctk.CTkEntry(
            sidebar,
            height=38,
            corner_radius=10,
            fg_color=theme.SURFACE,
            border_color=theme.BORDER,
            border_width=1,
            text_color=theme.TEXT,
            placeholder_text="e.g. microservices",
            placeholder_text_color=theme.MUTED,
        )
        self._topic.pack(pady=(0, 20), **padding)

        self._field_title(sidebar, f"Turns ({MIN_TURNS}–{MAX_TURNS})").pack(pady=(0, 6), **padding)
        self._turns = TurnStepper(sidebar)
        self._turns.pack(pady=(0, 24), **padding)

        self._start = ctk.CTkButton(
            sidebar,
            text="Start interview",
            height=42,
            corner_radius=10,
            font=theme.font(14, bold=True),
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.ON_ACCENT,
            text_color_disabled=theme.MUTED,
            command=self.start,
        )
        self._start.pack(**padding)

        self._open_report = ctk.CTkButton(
            sidebar,
            text="Open report",
            height=38,
            corner_radius=10,
            state="disabled",
            command=self.open_report,
            **theme.secondary_button_style(),
        )
        self._open_report.pack(side="bottom", pady=(0, 24), **padding)
        self._progress = ctk.CTkProgressBar(
            sidebar, height=6, fg_color=theme.BORDER, progress_color=theme.ACCENT
        )
        self._progress.set(0)
        self._progress.pack(side="bottom", pady=(0, 20), **padding)
        self._progress_label = self._field_title(sidebar, "Not started")
        self._progress_label.pack(side="bottom", pady=(0, 6), **padding)

    def _section_title(self, master: ctk.CTkFrame, text: str) -> ctk.CTkLabel:
        """Create the title of a section.

        Args:
            master: Parent widget.
            text: Title.

        Returns:
            The label.
        """
        return ctk.CTkLabel(
            master, text=text, text_color=theme.TEXT, font=theme.font(15, bold=True)
        )

    def _field_title(self, master: ctk.CTkFrame, text: str) -> ctk.CTkLabel:
        """Create the small title of a sidebar field.

        Args:
            master: Parent widget.
            text: Title.

        Returns:
            The label.
        """
        return ctk.CTkLabel(
            master, text=text, text_color=theme.MUTED, font=theme.font(12, bold=True), anchor="w"
        )

    def _poll_tasks(self) -> None:
        """Deliver the results of finished tasks and schedule the next check."""
        self._root.after(POLL_INTERVAL_MS, self._poll_tasks)
        self._tasks.deliver()

    def _set_status(self, text: str, *, alert: bool = False) -> None:
        """Show what is happening now.

        Args:
            text: Message for the user.
            alert: True for errors and while recording.
        """
        self._status.configure(text=text, text_color=theme.DANGER_TEXT if alert else theme.MUTED)

    def _set_setup_enabled(self, enabled: bool) -> None:
        """Allow or block setting up a new interview.

        Args:
            enabled: Whether the user can start an interview.
        """
        state = "normal" if enabled else "disabled"
        self._topic.configure(state=state)
        self._start.configure(state=state)
        self._turns.set_enabled(enabled)

    def _update_progress(self, session: InterviewSession) -> None:
        """Show how far along the interview is.

        Args:
            session: The current interview.
        """
        self._progress.set(session.answers_given / session.total_turns)
        if session.is_complete:
            self._progress_label.configure(text="All turns answered")
        else:
            self._progress_label.configure(
                text=f"Turn {session.current_turn} of {session.total_turns}"
            )

    def start(self) -> None:
        """Start a new interview with the chosen topic and number of turns."""
        self._speaker.stop()
        self._tasks.invalidate()
        session = InterviewSession(topic=self._topic.get().strip(), total_turns=self._turns.value)
        self._session = session
        self._saved_report = None
        self._chat.clear()
        self._corrections.clear()
        self._composer.set_text("")
        self._set_setup_enabled(False)
        self._open_report.configure(state="disabled")
        self._update_progress(session)
        self._set_status("The tutor is preparing the first question...")
        self._request_question(session)

    def _request_question(self, session: InterviewSession) -> None:
        """Ask for the tutor's next line in the background.

        Args:
            session: The current interview.
        """
        self._tasks.run(
            partial(self._coach.next_question, session),
            partial(self._on_question, session),
            partial(self._on_question_failed, session),
        )

    def _on_question(self, session: InterviewSession, question: str) -> None:
        """Show and read the tutor's question, and let the user answer.

        Args:
            session: The current interview.
            question: Text of the question.
        """
        session.add_question(question)
        self._chat.add_message(TUTOR_NAME, question, from_candidate=False)
        self._speaker.speak(question)
        self._composer.set_mode("ready")
        self._composer.focus_text()
        self._update_progress(session)
        self._set_status("Your turn: speak or type your answer.")

    def _on_question_failed(self, session: InterviewSession, error: Exception) -> None:
        """Let the user retry when the tutor could not reply.

        Args:
            session: The current interview.
            error: Error from the model call.
        """
        answer = session.discard_last_answer()
        if answer is None:
            self._set_setup_enabled(True)
            self._progress_label.configure(text="Not started")
            self._set_status(str(error), alert=True)
            return
        self._chat.remove_last()
        self._composer.set_mode("ready")
        self._composer.set_text(answer)
        self._update_progress(session)
        self._set_status(f"{error}\nYour answer is back in the box: send it again.", alert=True)

    def toggle_recording(self) -> None:
        """Start recording or, if already recording, finish and transcribe."""
        if self._recording:
            self._finish_recording()
            return

        self._speaker.stop()  # the microphone must not pick up the tutor's voice
        try:
            self._recorder.start()
        except Exception as error:  # sounddevice fails without a microphone or permission
            self._set_status(f"Could not open the microphone: {error}", alert=True)
            return
        self._recording = True
        self._composer.set_mode("recording")
        self._set_status("Recording... speak in English.", alert=True)

    def _finish_recording(self) -> None:
        """Close the microphone and transcribe the audio in the background."""
        audio = self._recorder.stop()
        self._recording = False
        if is_too_short(audio):
            self._composer.set_mode("ready")
            self._set_status("The recording is too short. Try again.", alert=True)
            return
        self._composer.set_mode("locked")
        self._set_status("Transcribing your answer...")
        self._tasks.run(
            partial(self._transcriber, audio), self._on_transcript, self._on_transcript_failed
        )

    def _on_transcript(self, text: str) -> None:
        """Process the transcript of a spoken answer.

        Args:
            text: The transcript; empty if no speech was detected.
        """
        if text:
            self._process_answer(text)
        else:
            self._composer.set_mode("ready")
            self._set_status("No speech detected. Check the microphone permission.", alert=True)

    def _on_transcript_failed(self, error: Exception) -> None:
        """Let the user answer again if the transcription fails.

        Args:
            error: Transcription error.
        """
        self._composer.set_mode("ready")
        self._set_status(f"Could not transcribe: {error}", alert=True)

    def send_text(self) -> None:
        """Send the answer written in the text box."""
        text = self._composer.text
        if not text or self._session is None:
            return
        self._speaker.stop()
        self._composer.set_text("")
        self._process_answer(text)

    def _process_answer(self, answer: str) -> None:
        """Record an answer, request its corrections and continue the interview.

        Corrections and the next question are requested in parallel, so that the interview
        does not wait for the corrections.

        Args:
            answer: Text of the user's answer.
        """
        session = self._session
        if session is None:
            return
        question = session.last_question
        turn = session.add_answer(answer)
        self._chat.add_message(CANDIDATE_NAME, answer, from_candidate=True)
        self._corrections.set_turn(turn, "Checking your answer...", pending=True)
        self._composer.set_mode("locked")
        self._update_progress(session)
        self._tasks.run(
            partial(self._coach.correct_answer, question, answer),
            partial(self._corrections.set_turn, turn),
            partial(self._on_correction_failed, turn),
        )
        if session.is_complete:
            self._set_status("Preparing your report...")
            self._tasks.run(
                partial(self._coach.conclude_interview, session, self._report_path),
                self._on_result,
                self._on_result_failed,
            )
        else:
            self._set_status("The tutor is thinking...")
            self._request_question(session)

    def _on_correction_failed(self, turn: int, error: Exception) -> None:
        """Note on the card of a turn that its corrections did not arrive.

        Args:
            turn: Affected turn.
            error: Error from the model call.
        """
        self._corrections.set_turn(turn, f"Not available. {error}")

    def _on_result(self, result: InterviewResult) -> None:
        """Show and read the final advice, and let the user open the report.

        Args:
            result: Outcome of the interview.
        """
        self._saved_report = result.report_path
        self._open_report.configure(state="normal")
        self._set_setup_enabled(True)
        self._set_status(f"Interview finished. Saved to {result.report_path}")
        if result.advice:
            self._chat.add_message("Final advice", result.advice, from_candidate=False)
            self._speaker.speak(result.advice)

    def _on_result_failed(self, error: Exception) -> None:
        """Report that the result could not be saved.

        Args:
            error: Error while saving.
        """
        self._set_setup_enabled(True)
        self._set_status(f"Could not save the report: {error}", alert=True)

    def open_report(self) -> None:
        """Open the saved report with the default macOS application."""
        if self._saved_report is not None:
            subprocess.run(["open", str(self._saved_report)], check=False)

    def close(self) -> None:
        """Stop the voice and the microphone before closing the window."""
        self._speaker.stop()
        if self._recording:
            self._recorder.stop()
        self._root.destroy()


def main() -> None:
    """Open the tutor window."""
    ctk.set_appearance_mode("system")
    root = ctk.CTk()
    TutorApp(root, Coach(ClaudeCliClient()), MacSpeaker(), Recorder())
    root.mainloop()


if __name__ == "__main__":
    main()
