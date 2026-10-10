import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from OWS.src.main import main


async def test_main_creates_named_tasks(monkeypatch):
    # Spy on create_task by putting tasks in a list
    created_tasks = []
    original_create_task = asyncio.create_task

    def spy_create_task(coro, **kwargs):
        task = original_create_task(coro, **kwargs)
        created_tasks.append(task)
        return task

    monkeypatch.setattr(asyncio, "create_task", spy_create_task)

    # Patch stop.wait to return immediately and prevent workers from running
    with patch("OWS.src.main.asyncio.Event") as mock_event:
        event = MagicMock()
        event.wait = AsyncMock()
        mock_event.return_value = event

        with patch("OWS.src.main.asyncio.get_running_loop", return_value=MagicMock()):
            await main(1)

    # Verify amount
    assert len(created_tasks) == 2
    # Verify those are tasks indeed
    for task in created_tasks:
        assert isinstance(task, asyncio.Task)
    # Verify names
    task_names = [task.get_name() for task in created_tasks]
    # This is not scalable. Should I rewrite it to work with any names and number of tasks?
    # What if name is not defined? Or should this test guarantee also the existence of names
    # for all tasks rather than only creation of those?
    assert "workload_task" in task_names
    assert "render_task" in task_names


async def test_main_runs_and_stops():
    """main() doesn't crash through its lifecycle."""

    async def fake_worker(*args, **kwargs):
        await asyncio.sleep(0.2)
        return None

    # We mock every worker since we don't need to actually run those.
    with patch("OWS.src.main.worker_workload", side_effect=fake_worker):
        with patch("OWS.src.main.worker_render", side_effect=fake_worker):
            with patch(
                "OWS.src.main.asyncio.get_running_loop", side_effect=MagicMock()
            ):
                with patch("OWS.src.main.asyncio.Event") as mock_event:
                    event = MagicMock()

                    async def short_wait():
                        await asyncio.sleep(0.05)

                    event.wait = short_wait
                    mock_event.return_value = event
                    await main(1)
