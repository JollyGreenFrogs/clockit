"""
Input validation and sanitization utilities
"""

import html
import re
from typing import Tuple


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent XSS and other injection attacks

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes
    value = value.replace("\x00", "")

    # Limit length
    value = value[:max_length]

    # HTML escape to prevent XSS
    value = html.escape(value)

    return value.strip()


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format

    Args:
        username: The username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 30:
        return False, "Username must be less than 30 characters"

    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return (
            False,
            "Username can only contain letters, numbers, underscores, and hyphens",
        )

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format

    Args:
        email: The email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    # Basic email validation pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    if len(email) > 254:  # RFC 5321
        return False, "Email address is too long"

    return True, ""


def validate_task_name(name: str) -> Tuple[bool, str]:
    """
    Validate task name

    Args:
        name: The task name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Task name cannot be empty"

    if len(name) > 200:
        return False, "Task name must be less than 200 characters"

    # Check for potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "\\", ";", "\x00"]
    if any(char in name for char in dangerous_chars):
        return False, "Task name contains invalid characters"

    return True, ""


def sanitize_description(description: str, max_length: int = 2000) -> str:
    """
    Sanitize description text

    Args:
        description: The description to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized description
    """
    if not description:
        return ""

    # Remove null bytes
    description = description.replace("\x00", "")

    # Limit length
    description = description[:max_length]

    # Basic HTML escape (allow newlines)
    description = html.escape(description)

    return description.strip()


def validate_numeric_input(
    value: float,
    min_value: float = None,
    max_value: float = None,
    field_name: str = "Value",
) -> Tuple[bool, str]:
    """
    Validate numeric input with optional range checking

    Args:
        value: The numeric value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, f"{field_name} must be a number"

    if min_value is not None and value < min_value:
        return False, f"{field_name} must be at least {min_value}"

    if max_value is not None and value > max_value:
        return False, f"{field_name} must be at most {max_value}"

    return True, ""


class ValidationError(Exception):
    """Custom validation error"""

    pass
