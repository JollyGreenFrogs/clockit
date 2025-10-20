import pytest


def test_create_task_and_add_time_entry(tmp_path):
    """Test legacy file-based TaskManager - skipped as API has migrated to database"""
    pytest.skip(
        "Legacy file-based TaskManager API is deprecated. Use test_task_manager_new.py for current tests."
    )
