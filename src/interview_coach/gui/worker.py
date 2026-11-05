"""Runs slow work outside the Tkinter thread."""

import queue
import threading
from collections.abc import Callable
from functools import partial
from typing import TypeVar

T = TypeVar("T")


class BackgroundTasks:
    """Runs tasks in threads and hands results back to the thread that calls ``deliver``.

    Tkinter can only be used from its own thread, so callbacks wait in a queue until the
    interface drains it. Results from before the last ``invalidate`` are dropped.
    """

    def __init__(self) -> None:
        """Create an empty task runner."""
        self._callbacks: queue.Queue[Callable[[], None]] = queue.Queue()
        self._generation = 0

    def run(
        self,
        task: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        """Run a task in a new thread.

        Args:
            task: Work to run outside the interface thread.
            on_success: Receives the result when ``deliver`` is called.
            on_error: Receives the error when ``deliver`` is called.
        """
        generation = self._generation

        def work() -> None:
            """Run the task and queue its outcome."""
            try:
                result = task()
            except Exception as error:  # a thread must not die without telling the interface
                self._callbacks.put(partial(self._hand_over, generation, on_error, error))
            else:
                self._callbacks.put(partial(self._hand_over, generation, on_success, result))

        threading.Thread(target=work, daemon=True).start()

    def invalidate(self) -> None:
        """Drop the results of every task started so far."""
        self._generation += 1

    def deliver(self) -> None:
        """Call the callbacks of finished tasks; call it from the interface thread."""
        while True:
            try:
                callback = self._callbacks.get_nowait()
            except queue.Empty:
                return
            callback()

    def _hand_over(self, generation: int, callback: Callable[[T], None], value: T) -> None:
        """Pass a value to its callback unless it has been invalidated.

        Args:
            generation: Generation in which the task started.
            callback: Function that receives the value.
            value: Result or error of the task.
        """
        if generation == self._generation:
            callback(value)
