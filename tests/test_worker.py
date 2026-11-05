import threading
import time
from collections.abc import Callable

from interview_coach.gui.worker import BackgroundTasks


def wait_for(tasks: BackgroundTasks, done: Callable[[], bool]) -> None:
    deadline = time.monotonic() + 5
    while not done() and time.monotonic() < deadline:
        tasks.deliver()
        time.sleep(0.01)
    assert done()


def fail() -> str:
    raise RuntimeError("boom")


def test_delivers_result_and_error() -> None:
    tasks = BackgroundTasks()
    results: list[str] = []
    errors: list[str] = []
    tasks.run(lambda: "ok", results.append, lambda error: errors.append(str(error)))
    tasks.run(fail, results.append, lambda error: errors.append(str(error)))
    wait_for(tasks, lambda: bool(results and errors))
    assert results == ["ok"]
    assert errors == ["boom"]


def test_invalidate_drops_results_of_earlier_tasks() -> None:
    tasks = BackgroundTasks()
    results: list[str] = []
    release = threading.Event()

    def slow() -> str:
        release.wait(5)
        return "old"

    tasks.run(slow, results.append, lambda _error: None)
    tasks.invalidate()
    release.set()
    tasks.run(lambda: "new", results.append, lambda _error: None)
    wait_for(tasks, lambda: "new" in results)
    time.sleep(0.05)
    tasks.deliver()
    assert results == ["new"]
