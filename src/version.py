#!/usr/bin/env python3
"""
Version management for ClockIt
"""

__version__ = "1.0.2"
__build_date__ = "2025-08-06"
__author__ = "ClockIt Development Team"

VERSION_INFO = {
    "version": __version__,
    "build_date": __build_date__,
    "author": __author__,
    "description": "Professional Time Tracking & Invoice Generation"
}

def get_version():
    """Get the current version string"""
    return __version__

def get_full_version_info():
    """Get complete version information"""
    return VERSION_INFO

def get_version_string():
    """Get formatted version string for display"""
    return f"ClockIt v{__version__} ({__build_date__})"
