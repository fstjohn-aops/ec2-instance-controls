#!/bin/bash

# Simple Test Runner for EC2 Instance
# This script will run the appropriate tests based on what's available

echo "🚀 EC2 Slack Bot Test Runner"
echo "============================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this from the backend directory."
    exit 1
fi

# Check if Python test suite exists
if [ -f "test_suite.py" ]; then
    echo "✅ Found Python test suite"
    echo "Running comprehensive Python tests..."
    python3 test_suite.py
    PYTHON_EXIT_CODE=$?
else
    echo "⚠️  Python test suite not found"
    PYTHON_EXIT_CODE=1
fi

# Check if improved test runner exists
if [ -f "run_tests_improved.sh" ]; then
    echo ""
    echo "✅ Found improved test runner"
    echo "Running improved test suite..."
    ./run_tests_improved.sh
    IMPROVED_EXIT_CODE=$?
else
    echo "⚠️  Improved test runner not found"
    IMPROVED_EXIT_CODE=1
fi

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================"

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    echo "✅ Python test suite: PASSED"
else
    echo "❌ Python test suite: FAILED"
fi

if [ $IMPROVED_EXIT_CODE -eq 0 ]; then
    echo "✅ Improved test suite: PASSED"
else
    echo "❌ Improved test suite: FAILED"
fi

# Overall result
if [ $PYTHON_EXIT_CODE -eq 0 ] || [ $IMPROVED_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 At least one test suite passed!"
    echo "Your EC2 Slack Bot is ready for deployment."
    exit 0
else
    echo ""
    echo "❌ All test suites failed."
    echo "Please check the output above for details."
    exit 1
fi 