#!/usr/bin/env python3
"""
Test runner for EC2 Instance Control App
"""

import pytest
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run all tests"""
    print("Running EC2 Instance Control App tests...")
    
    # Run tests in test directory
    test_dir = os.path.join(os.path.dirname(__file__), 'test')
    result = pytest.main([test_dir, '-v'])
    
    if result == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return result

if __name__ == '__main__':
    sys.exit(run_tests()) 