from pathlib import Path
from src.business.task_manager import TaskManager


def test_create_task_and_add_time_entry(tmp_path):
    data_dir = tmp_path / "clockit_data"
    data_dir.mkdir()

    tm = TaskManager(data_dir)

    # Create a task
    task = tm.create_task("Test Task", description="A task for testing")
    assert task["name"] == "Test Task"
    task_id = task["id"]

    # Add a time entry
    success = tm.add_time_entry(task_id, hours=2.5, date="2025-09-26", description="Worked on feature")
    assert success

    # Reload tasks and verify
    loaded = tm.load_tasks()
    assert task_id in loaded["tasks"]
    assert loaded["tasks"][task_id]["total_hours"] == 2.5
    assert len(loaded["tasks"][task_id]["time_entries"]) == 1
