"""
Integration test to verify main.py refactoring works correctly
This tests that main.py can use the new data_models instead of inline Pydantic models
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient


def test_main_app_imports_new_models():
    """Test that main.py can import and use the new data models"""
    try:
        # This will fail if main.py can't import our new models
        from main import app
        print("✅ main.py successfully imported with new data models")
    except ImportError as e:
        pytest.fail(f"main.py failed to import new data models: {e}")


def test_fastapi_endpoints_use_new_models():
    """Test that FastAPI endpoints work with the refactored models"""
    from main import app
    
    client = TestClient(app)
    
    # Test that the app starts correctly with new models
    response = client.get("/")
    assert response.status_code == 200
    assert "ClockIt API Server" in response.json()["message"]
    
    # Test that endpoints that use our models are accessible
    # (This verifies the imports worked)
    response = client.get("/health")
    assert response.status_code == 200


def test_task_manager_integration_with_new_time_entry():
    """
    Test that TaskManager works with the new TimeEntry model structure
    This is the CRITICAL test - verifying our datetime refactoring works
    """
    from business.task_manager import TaskManager
    from data_models.requests import TimeEntry
    
    # Create a TaskManager instance
    task_manager = TaskManager()
    
    # Create a TimeEntry with the new structure (datetime instead of string)
    time_entry = TimeEntry(
        hours=2.5,
        date=datetime.now(),
        description="Test time entry with datetime"
    )
    
    # Verify the TaskManager method signature accepts our new model
    # This would fail if the refactoring wasn't complete
    try:
        # We can't actually call this without a database, but we can verify the signature
        import inspect
        signature = inspect.signature(task_manager.add_time_entry_by_id)
        params = signature.parameters
        
        # Verify the method expects a TimeEntry model (not individual parameters)
        assert 'time_entry' in params
        assert 'task_id' in params
        assert 'user_id' in params
        
        # Verify it doesn't have the old individual parameters
        assert 'duration' not in params
        assert 'date' not in params
        assert 'description' not in params
        
        print("✅ TaskManager.add_time_entry_by_id has correct signature for new TimeEntry model")
        
    except Exception as e:
        pytest.fail(f"TaskManager integration failed: {e}")


def test_time_entry_datetime_validation():
    """
    Test that the datetime field actually provides validation benefits
    This is WHY we made the change from string to datetime
    """
    from data_models.requests import TimeEntry
    from pydantic import ValidationError
    
    # Valid datetime should work
    valid_entry = TimeEntry(
        hours=1.0,
        date=datetime.now(),
        description="Valid entry"
    )
    assert isinstance(valid_entry.date, datetime)
    
    # Test that string dates are automatically converted to datetime
    string_date_entry = TimeEntry(
        hours=1.0,
        date="2024-10-27T14:30:00",  # ISO format string
        description="String date that should convert"
    )
    assert isinstance(string_date_entry.date, datetime)
    
    # Invalid date format should fail
    with pytest.raises(ValidationError):
        TimeEntry(
            hours=1.0,
            date="invalid-date-format",
            description="This should fail"
        )
    
    print("✅ DateTime validation working correctly - this is the benefit of our refactoring!")


def test_pydantic_models_separation():
    """
    Test that we successfully separated request and response models
    """
    # Test imports work correctly
    from data_models.requests import (
        TimeEntry, TimeEntryUpdate, TaskCreate, TaskCategoryUpdate,
        OnboardingData, RateConfig, CurrencyConfig
    )
    from data_models.responses import OnboardingStatus
    
    # Verify OnboardingStatus is NOT in requests (it's a response model)
    try:
        from data_models.requests import OnboardingStatus
        pytest.fail("OnboardingStatus should be in responses, not requests!")
    except ImportError:
        pass  # This is expected
    
    print("✅ Request/Response models properly separated")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])