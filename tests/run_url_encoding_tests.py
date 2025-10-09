#!/usr/bin/env python3
"""
Test runner for URL encoding fix tests

This script runs the automated tests for the URL encoding fix
and provides detailed output about the test results.
"""

import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_url_encoding_manually():
    """Manual test of URL encoding scenarios"""
    print("🧪 Manual URL Encoding Tests")
    print("=" * 50)

    test_cases = [
        "General IT/Tech work",
        "Project A/B Testing",
        "Client/Server Development",
        "UI/UX Design",
        "Data Analysis & Reports",
        "Meeting (Project #1)",
    ]
    
    all_passed = True
    
    for task_name in test_cases:
        encoded = urllib.parse.quote(task_name)
        decoded = urllib.parse.unquote(encoded)
        
        print(f"Original:  '{task_name}'")
        print(f"Encoded:   '{encoded}'")
        print(f"Decoded:   '{decoded}'")
        
        if decoded == task_name:
            print("✅ PASS: Round-trip encoding/decoding successful")
        else:
            print("❌ FAIL: Round-trip encoding/decoding failed")
            all_passed = False
        
        print("-" * 30)
    
    return all_passed

def test_api_endpoints():
    """Test API endpoints with curl"""
    print("\n🌐 API Endpoint Tests")
    print("=" * 50)

    # Check if backend is running
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8001/health"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            print("✅ Backend is running on http://localhost:8001")
            return True
        else:
            print("❌ Backend is not responding")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Backend health check timed out")
        return False
    except FileNotFoundError:
        print("❌ curl command not found")
        return False


def run_pytest():
    """Run pytest on the URL encoding test file"""
    print("\n🧪 Running Automated Tests with pytest")
    print("=" * 50)
    
    test_file = Path(__file__).parent / "test_url_encoding_fix.py"
    
    try:
        # Run pytest with verbose output
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": str(src_path)},
            text=True,
        )

        if result.returncode == 0:
            print("✅ All pytest tests passed!")
            return True
        else:
            print("❌ Some pytest tests failed")
            return False

    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False


def main():
    """Run all tests"""
    print("🔧 ClockIt URL Encoding Fix - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Manual URL encoding tests
    print("\n📋 Test 1: URL Encoding/Decoding Logic")
    results.append(test_url_encoding_manually())
    
    # Test 2: Check if backend is running
    print("\n📋 Test 2: Backend Availability")
    results.append(test_api_endpoints())
    
    # Test 3: Run automated tests
    print("\n📋 Test 3: Automated Test Suite")
    results.append(run_pytest())
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    test_names = ["URL Encoding Logic", "Backend Availability", "Automated Tests"]
    
    for i, (name, passed) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    all_passed = all(results)
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🚀 The URL encoding fix is working correctly!")
        print("   You can now deploy to production with confidence.")
    else:
        print("\n🔧 Some tests failed. Please review the output above.")
        print("   Make sure the backend is running on http://localhost:8001")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
