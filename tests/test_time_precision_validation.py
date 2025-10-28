"""
Test time precision validation for small duration values.

This test ensures that very small time durations (like 1-10 seconds)
are properly validated and saved without being truncated to 0.
"""

import pytest
from pydantic import ValidationError

from src.data_models.requests import TimeEntry, TimeEntryCreate, TimeEntryUpdate


class TestTimePrecisionValidation:
    """Test precision validation for time entry models"""

    def test_time_entry_accepts_small_durations(self):
        """Test that TimeEntry accepts very small hour values"""
        # 1 second = 0.000278 hours (rounded to 6 decimal places)
        one_second_in_hours = round(1 / 3600, 6)
        
        # 5 seconds = 0.001389 hours (rounded to 6 decimal places)
        five_seconds_in_hours = round(5 / 3600, 6)
        
        # 10 seconds = 0.002778 hours (rounded to 6 decimal places)
        ten_seconds_in_hours = round(10 / 3600, 6)
        
        # Test that these small values are accepted
        time_entry_1s = TimeEntry(
            hours=one_second_in_hours,
            date="2025-10-28",
            description="1 second test"
        )
        assert time_entry_1s.hours == one_second_in_hours
        
        time_entry_5s = TimeEntry(
            hours=five_seconds_in_hours,
            date="2025-10-28",
            description="5 seconds test"
        )
        assert time_entry_5s.hours == five_seconds_in_hours
        
        time_entry_10s = TimeEntry(
            hours=ten_seconds_in_hours,
            date="2025-10-28",
            description="10 seconds test"
        )
        assert time_entry_10s.hours == ten_seconds_in_hours

    def test_time_entry_create_accepts_small_durations(self):
        """Test that TimeEntryCreate accepts very small duration values"""
        # Test various small durations
        durations_to_test = [
            1 / 3600,      # 1 second
            3.7 / 3600,    # 3.7 seconds (from user's test case)
            6.2 / 3600,    # 6.2 seconds (from user's test case)
            0.000278,      # Approximately 1 second
            0.001721,      # Approximately 6.2 seconds
        ]
        
        for duration in durations_to_test:
            time_entry = TimeEntryCreate(
                task_name="Test Task",
                duration=duration,
                description=f"Test with {duration * 3600:.1f} seconds"
            )
            assert time_entry.duration == duration

    def test_time_entry_update_accepts_small_durations(self):
        """Test that TimeEntryUpdate accepts very small duration values"""
        small_duration = 0.000278  # ~1 second
        
        time_entry_update = TimeEntryUpdate(
            duration=small_duration,
            description="Updated with small duration"
        )
        assert time_entry_update.duration == small_duration

    def test_minimum_validation_boundary(self):
        """Test the minimum validation boundary (0.000001 hours)"""
        # This should pass (at the boundary)
        time_entry = TimeEntry(
            hours=0.000001,
            date="2025-10-28",
            description="Minimum boundary test"
        )
        assert time_entry.hours == 0.000001
        
        # This should fail (below the boundary)
        with pytest.raises(ValidationError) as exc_info:
            TimeEntry(
                hours=0.0000005,  # Half of minimum
                date="2025-10-28",
                description="Below minimum test"
            )
        
        # Check that it's a validation error for the hours field
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("hours" in str(error) for error in errors)

    def test_zero_duration_rejected(self):
        """Test that zero duration is properly rejected"""
        with pytest.raises(ValidationError):
            TimeEntry(
                hours=0.0,
                date="2025-10-28",
                description="Zero duration test"
            )
        
        with pytest.raises(ValidationError):
            TimeEntryCreate(
                task_name="Test Task",
                duration=0.0,
                description="Zero duration test"
            )

    def test_negative_duration_rejected(self):
        """Test that negative durations are properly rejected"""
        with pytest.raises(ValidationError):
            TimeEntry(
                hours=-0.1,
                date="2025-10-28",
                description="Negative duration test"
            )
        
        with pytest.raises(ValidationError):
            TimeEntryCreate(
                task_name="Test Task",
                duration=-1.0,
                description="Negative duration test"
            )

    def test_maximum_duration_boundary(self):
        """Test that 24-hour maximum is still enforced"""
        # This should pass (at the boundary)
        time_entry = TimeEntry(
            hours=24.0,
            date="2025-10-28",
            description="Maximum boundary test"
        )
        assert time_entry.hours == 24.0
        
        # This should fail (above the boundary)
        with pytest.raises(ValidationError):
            TimeEntry(
                hours=24.1,
                date="2025-10-28",
                description="Above maximum test"
            )

    def test_realistic_timer_scenarios(self):
        """Test realistic timer scenarios from actual usage"""
        # Test scenarios based on the user's reported issues
        scenarios = [
            {
                "name": "6.2 second timer session",
                "milliseconds": 6200,
                "expected_hours": 6200 / (1000 * 60 * 60)  # Convert ms to hours
            },
            {
                "name": "3.7 second timer session",
                "milliseconds": 3700,
                "expected_hours": 3700 / (1000 * 60 * 60)
            },
            {
                "name": "1 second timer session",
                "milliseconds": 1000,
                "expected_hours": 1000 / (1000 * 60 * 60)
            },
            {
                "name": "30 second timer session",
                "milliseconds": 30000,
                "expected_hours": 30000 / (1000 * 60 * 60)
            }
        ]
        
        for scenario in scenarios:
            # Round to 6 decimal places as done in the validator
            hours = round(scenario["expected_hours"], 6)
            
            time_entry = TimeEntry(
                hours=hours,
                date="2025-10-28",
                description=f"Timer: {scenario['milliseconds']/1000:.1f} seconds"
            )
            
            assert time_entry.hours == hours
            print(f"✅ {scenario['name']}: {hours} hours ({scenario['milliseconds']/1000:.1f}s) - PASSED")

    def test_precision_rounding_consistency(self):
        """Test that precision rounding is consistent with frontend calculations"""
        # Simulate the frontend calculation from App.jsx
        test_cases = [
            {"ms": 6200, "description": "6.2 second session"},
            {"ms": 3700, "description": "3.7 second session"},
            {"ms": 1000, "description": "1 second session"},
            {"ms": 500, "description": "0.5 second session"},
        ]
        
        for case in test_cases:
            # Frontend calculation: timeToSave / (1000 * 60 * 60)
            hours_raw = case["ms"] / (1000 * 60 * 60)
            # Frontend rounding: Math.round(hours * 1000000) / 1000000
            hours_rounded = round(hours_raw, 6)
            
            # Ensure our validation accepts this value
            time_entry = TimeEntry(
                hours=hours_rounded,
                date="2025-10-28",
                description=case["description"]
            )
            
            assert time_entry.hours == hours_rounded
            print(f"✅ {case['description']}: {hours_rounded} hours - PASSED")


if __name__ == "__main__":
    # Run the tests directly if this file is executed
    test = TestTimePrecisionValidation()
    
    print("Testing time precision validation...")
    test.test_time_entry_accepts_small_durations()
    test.test_time_entry_create_accepts_small_durations()
    test.test_time_entry_update_accepts_small_durations()
    test.test_minimum_validation_boundary()
    test.test_realistic_timer_scenarios()
    test.test_precision_rounding_consistency()
    print("✅ All precision validation tests passed!")