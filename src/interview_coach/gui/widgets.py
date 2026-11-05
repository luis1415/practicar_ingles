"""Reusable pieces of the desktop interface."""

import tkinter as tk
from collections.abc import Callable

import customtkinter as ctk

from interview_coach.config import DEFAULT_TURNS, MAX_TURNS, MIN_TURNS
from interview_coach.gui import theme

BUBBLE_WIDTH_RATIO = 0.78
MIN_WRAP_LENGTH = 160


class TurnStepper(ctk.CTkFrame):
    """Lets the user choose how many turns the interview has."""

    def __init__(self, master: tk.Misc) -> None:
        """Create the stepper with the default number of turns.

        Args:
            master: Parent widget.
        """
        super().__init__(master, fg_color="transparent")
        self._value = DEFAULT_TURNS
        self._decrease = self._create_button("−", -1)
        self._decrease.pack(side="left")
        self._label = ctk.CTkLabel(self, font=theme.font(16, bold=True), text_color=theme.TEXT)
        self._label.pack(side="left", expand=True)
        self._increase = self._create_button("+", 1)
        self._increase.pack(side="right")
        self._refresh(enabled=True)

    @property
    def value(self) -> int:
        """Currently selected number of turns."""
        return self._value

    def set_enabled(self, enabled: bool) -> None:
        """Allow or block changes.

        Args:
            enabled: Whether the user can change the value.
        """
        self._refresh(enabled)

    def _create_button(self, text: str, step: int) -> ctk.CTkButton:
        """Create one of the two stepper buttons.

        Args:
            text: Button symbol.
            step: Amount added to the value when clicked.

        Returns:
            The button.
        """
        return ctk.CTkButton(
            self,
            text=text,
            width=38,
            height=38,
            corner_radius=10,
            font=theme.font(18),
            command=lambda: self._change(step),
            **theme.secondary_button_style(),
        )

    def _change(self, step: int) -> None:
        """Change the value, staying within the allowed range.

        Args:
            step: Amount to add.
        """
        self._value = max(MIN_TURNS, min(MAX_TURNS, self._value + step))
        self._refresh(enabled=True)

    def _refresh(self, enabled: bool) -> None:
        """Update the label and which buttons can be used.

        Args:
            enabled: Whether the user can change the value.
        """
        self._label.configure(text=str(self._value))
        can_decrease = enabled and self._value > MIN_TURNS
        can_increase = enabled and self._value < MAX_TURNS
        self._decrease.configure(state="normal" if can_decrease else "disabled")
        self._increase.configure(state="normal" if can_increase else "disabled")


class ScrollingColumn(ctk.CTkScrollableFrame):
    """A scrolling list of messages whose text wraps to the available width."""

    def __init__(self, master: tk.Misc, empty_text: str) -> None:
        """Create an empty column.

        Args:
            master: Parent widget.
            empty_text: Hint shown while the column has no content.
        """
        super().__init__(
            master,
            fg_color="transparent",
            scrollbar_button_color=theme.BORDER,
            scrollbar_button_hover_color=theme.MUTED,
        )
        self._rows: list[ctk.CTkFrame] = []
        self._wrapped: list[ctk.CTkLabel] = []
        self._wrap_length = MIN_WRAP_LENGTH
        self._empty_hint = ctk.CTkLabel(
            self,
            text=empty_text,
            text_color=theme.MUTED,
            font=theme.font(13),
            wraplength=MIN_WRAP_LENGTH,
            justify="center",
        )
        self._empty_hint.pack(pady=40, padx=theme.GAP)
        self.bind("<Configure>", self._on_resize)

    def clear(self) -> None:
        """Remove all the content and show the hint again."""
        for row in self._rows:
            row.destroy()
        self._rows = []
        self._wrapped = []
        self._empty_hint.pack(pady=40, padx=theme.GAP)

    def remove_last(self) -> None:
        """Remove the last row."""
        if self._rows:
            self._rows.pop().destroy()

    def _add_row(self) -> ctk.CTkFrame:
        """Add a transparent row at the end.

        Returns:
            The new row.
        """
        self._empty_hint.pack_forget()
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(0, theme.SMALL_GAP + 2))
        self._rows.append(row)
        return row

    def _add_wrapped_label(self, master: tk.Misc, text: str, color: theme.Color) -> ctk.CTkLabel:
        """Add body text that wraps to the column width.

        Args:
            master: Parent widget.
            text: Text to show.
            color: Text color.

        Returns:
            The label.
        """
        label = ctk.CTkLabel(
            master,
            text=text,
            text_color=color,
            font=theme.font(14),
            wraplength=self._wrap_length,
            justify="left",
            anchor="w",
        )
        self._wrapped.append(label)
        return label

    def _scroll_to_end(self) -> None:
        """Show the latest content once the layout has been updated."""
        self.after(30, lambda: self._parent_canvas.yview_moveto(1.0))

    def _on_resize(self, event: "tk.Event[tk.Misc]") -> None:
        """Rewrap the text when the available width changes.

        Args:
            event: Tkinter resize event.
        """
        scaling = self._get_widget_scaling()
        self._wrap_length = max(MIN_WRAP_LENGTH, int(event.width / scaling * BUBBLE_WIDTH_RATIO))
        self._wrapped = [label for label in self._wrapped if label.winfo_exists()]
        for label in self._wrapped:
            label.configure(wraplength=self._wrap_length)
        self._empty_hint.configure(wraplength=self._wrap_length)


class ChatView(ScrollingColumn):
    """The conversation, as chat bubbles."""

    def add_message(self, author: str, text: str, *, from_candidate: bool) -> None:
        """Add a chat bubble.

        Args:
            author: Name shown above the text.
            text: Message text.
            from_candidate: True to align it to the right with the accent color.
        """
        row = self._add_row()
        side = "e" if from_candidate else "w"
        ctk.CTkLabel(row, text=author, text_color=theme.MUTED, font=theme.font(12, bold=True)).pack(
            anchor=side, padx=6, pady=(0, 2)
        )
        bubble = ctk.CTkFrame(
            row,
            fg_color=theme.ACCENT if from_candidate else theme.SURFACE,
            border_width=0 if from_candidate else 1,
            border_color=theme.BORDER,
            corner_radius=theme.RADIUS,
        )
        bubble.pack(anchor=side)
        color = theme.ON_ACCENT if from_candidate else theme.TEXT
        self._add_wrapped_label(bubble, text, color).pack(padx=14, pady=10)
        self._scroll_to_end()


class CorrectionsView(ScrollingColumn):
    """The corrections of each turn, as cards in turn order."""

    def __init__(self, master: tk.Misc, empty_text: str) -> None:
        """Create an empty list of corrections.

        Args:
            master: Parent widget.
            empty_text: Hint shown while there are no corrections.
        """
        super().__init__(master, empty_text)
        self._cards: dict[int, ctk.CTkLabel] = {}

    def clear(self) -> None:
        """Remove every card."""
        super().clear()
        self._cards = {}

    def set_turn(self, turn: int, text: str, *, pending: bool = False) -> None:
        """Show the text of a turn, creating its card the first time.

        Args:
            turn: Turn the corrections belong to.
            text: Text to show.
            pending: True while the corrections are still being prepared.
        """
        color = theme.MUTED if pending else theme.TEXT
        label = self._cards.get(turn)
        if label is None:
            card = ctk.CTkFrame(
                self._add_row(),
                fg_color=theme.SURFACE,
                border_width=1,
                border_color=theme.BORDER,
                corner_radius=theme.RADIUS,
            )
            card.pack(fill="x")
            ctk.CTkLabel(
                card,
                text=f"Turn {turn}",
                text_color=theme.ACCENT_TEXT,
                font=theme.font(12, bold=True),
                anchor="w",
            ).pack(fill="x", padx=14, pady=(10, 0))
            label = self._add_wrapped_label(card, text, color)
            label.pack(fill="x", padx=14, pady=(2, 10))
            self._cards[turn] = label
            self._scroll_to_end()
        else:
            label.configure(text=text, text_color=color)


class Composer(ctk.CTkFrame):
    """Where the user writes or records an answer."""

    def __init__(
        self, master: tk.Misc, on_send: Callable[[], None], on_toggle_record: Callable[[], None]
    ) -> None:
        """Create the composer.

        Args:
            master: Parent widget.
            on_send: Called when the user sends the written text.
            on_toggle_record: Called when the user presses the record button.
        """
        super().__init__(
            master,
            fg_color=theme.SURFACE,
            border_width=1,
            border_color=theme.BORDER,
            corner_radius=theme.RADIUS,
        )
        self._on_send = on_send
        self.columnconfigure(0, weight=1)
        self._textbox = ctk.CTkTextbox(
            self,
            height=64,
            fg_color="transparent",
            text_color=theme.TEXT,
            font=theme.font(14),
            wrap="word",
            activate_scrollbars=False,
        )
        self._textbox.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(8, 4), pady=8)
        self._textbox.bind("<Return>", self._on_return)
        self._textbox.bind("<Shift-Return>", lambda _event: None)

        self._send = ctk.CTkButton(
            self,
            text="Send",
            width=132,
            height=32,
            corner_radius=10,
            font=theme.font(13, bold=True),
            command=on_send,
            **theme.secondary_button_style(),
        )
        self._send.grid(row=0, column=1, padx=(4, 10), pady=(10, 3))
        self._record = ctk.CTkButton(
            self,
            text="● Record",
            width=132,
            height=32,
            corner_radius=10,
            font=theme.font(13, bold=True),
            text_color=theme.ON_ACCENT,
            text_color_disabled=theme.MUTED,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=on_toggle_record,
        )
        self._record.grid(row=1, column=1, padx=(4, 10), pady=(3, 10))

    @property
    def text(self) -> str:
        """The written answer, without surrounding whitespace."""
        return str(self._textbox.get("1.0", "end")).strip()

    def set_text(self, text: str) -> None:
        """Replace the written answer.

        Args:
            text: New text.
        """
        state = self._textbox.cget("state")
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", text)
        self._textbox.configure(state=state)

    def focus_text(self) -> None:
        """Put the keyboard focus on the text box."""
        self._textbox.focus_set()

    def set_mode(self, mode: str) -> None:
        """Change which controls can be used.

        Args:
            mode: ``"ready"`` to answer, ``"recording"`` while recording, ``"locked"`` otherwise.
        """
        ready = mode == "ready"
        recording = mode == "recording"
        self._textbox.configure(state="normal" if ready else "disabled")
        self._send.configure(state="normal" if ready else "disabled")
        self._record.configure(
            state="normal" if ready or recording else "disabled",
            text="■ Stop and send" if recording else "● Record",
            fg_color=theme.DANGER if recording else theme.ACCENT,
            hover_color=theme.DANGER_HOVER if recording else theme.ACCENT_HOVER,
        )

    def _on_return(self, _event: object) -> str:
        """Send the answer when Enter is pressed.

        Returns:
            ``"break"``, so that Tkinter does not also insert a line break.
        """
        self._on_send()
        return "break"
