#!/usr/bin/env python3
"""
Test URL normalization functions
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import normalize_url, normalize_socket_io_path

def test_normalize_url():
    """Test URL normalization function"""
    print("Testing normalize_url function...")
    
    test_cases = [
        ("https://example.com", "https://example.com"),
        ("https://example.com/", "https://example.com"),
        ("https://example.com//", "https://example.com"),
        ("https://example.com/api/", "https://example.com/api"),
        ("https://example.com/api//", "https://example.com/api"),
        ("/", "/"),  # Root should stay as is
        ("", ""),  # Empty should stay empty
        (None, None),  # None should stay None
    ]
    
    all_passed = True
    for input_url, expected in test_cases:
        result = normalize_url(input_url) if input_url is not None else normalize_url(input_url)
        if result != expected:
            print(f"❌ FAIL: normalize_url('{input_url}') = '{result}', expected '{expected}'")
            all_passed = False
        else:
            print(f"✅ PASS: normalize_url('{input_url}') = '{result}'")
    
    return all_passed

def test_normalize_socket_io_path():
    """Test Socket.IO path normalization function"""
    print("\nTesting normalize_socket_io_path function...")
    
    test_cases = [
        ("/socket.io/", "/socket.io/"),
        ("/socket.io", "/socket.io/"),
        ("socket.io/", "/socket.io/"),
        ("socket.io", "/socket.io/"),
        ("", "/socket.io/"),  # Empty gets default
        (None, "/socket.io/"),  # None gets default
        ("/custom/path/", "/custom/path/"),
        ("/custom/path", "/custom/path/"),
        ("custom/path", "/custom/path/"),
    ]
    
    all_passed = True
    for input_path, expected in test_cases:
        result = normalize_socket_io_path(input_path) if input_path is not None else normalize_socket_io_path(input_path)
        if result != expected:
            print(f"❌ FAIL: normalize_socket_io_path('{input_path}') = '{result}', expected '{expected}'")
            all_passed = False
        else:
            print(f"✅ PASS: normalize_socket_io_path('{input_path}') = '{result}'")
    
    return all_passed

def main():
    """Run all tests"""
    print("🧪 Testing URL Normalization Functions")
    print("=" * 50)
    
    url_tests_passed = test_normalize_url()
    socket_tests_passed = test_normalize_socket_io_path()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if url_tests_passed and socket_tests_passed:
        print("🎉 All normalization tests passed!")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
