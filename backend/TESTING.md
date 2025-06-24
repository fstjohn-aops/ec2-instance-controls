# Testing Guide for EC2 Slack Bot

## Overview

The EC2 Slack Bot uses a simplified, modular test architecture that replaces the previous complex shell scripts with clean, maintainable Python-based tests.

## Quick Start

### Run All Tests
```bash
cd backend
python3 run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python3 -m pytest tests/ -m unit -v

# Integration tests only  
python3 -m pytest tests/ -m integration -v

# API tests only
python3 -m pytest tests/test_api.py -v

# Database tests only
python3 -m pytest tests/test_database.py -v
```

## Test Architecture

### 📁 Test Structure
```
tests/
├── __init__.py          # Package marker
├── conftest.py          # Pytest configuration & fixtures
├── test_api.py          # API endpoint tests
├── test_database.py     # Database operation tests
├── test_ec2.py          # EC2 operations tests
├── test_integration.py  # End-to-end integration tests
├── test_environment.py  # Environment & system tests
└── README.md           # Detailed test documentation
```

### 🧪 Test Categories

1. **Unit Tests** - Fast, isolated component tests
   - API endpoints with Flask test client
   - Database operations with temporary databases
   - EC2 operations with mocked AWS responses

2. **Integration Tests** - End-to-end workflow tests
   - Complete assignment flows
   - Slack command simulation
   - Error handling scenarios

3. **Environment Tests** - System requirement validation
   - Python version checks
   - Package availability
   - Docker availability (optional)

## Test Runner Features

### 🔧 Automatic Setup
- ✅ Python version validation (3.8+)
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Environment file creation
- ✅ Test database setup

### 🐳 Docker Testing (Optional)
- ✅ Docker availability detection
- ✅ Container build and test
- ✅ Health endpoint validation
- ✅ Automatic cleanup

### 📊 Clear Results
- ✅ Verbose test output
- ✅ Pass/fail indicators
- ✅ Error details for debugging
- ✅ Summary with next steps

## Test Data Management

### Database Testing
- Uses temporary SQLite databases
- Pre-populated with test data
- Automatic cleanup after tests
- Isolated from production data

### Environment Variables
- Test-specific configuration
- Mock credentials for external services
- Automatic restoration after tests

## Debugging Tests

### Verbose Output
```bash
python3 -m pytest tests/ -v -s --tb=long
```

### Test Specific Component
```bash
# Test single function
python3 -m pytest tests/test_api.py::TestHealthEndpoint::test_health_check -v

# Test with print statements
python3 -m pytest tests/test_integration.py -v -s
```

### Common Issues

1. **Import Errors**
   - Ensure you're in the `backend` directory
   - Check that virtual environment is activated

2. **Database Errors**
   - Tests use temporary databases
   - No manual cleanup required
   - Check file permissions

3. **Network Errors**
   - Integration tests require localhost access
   - Docker tests require Docker daemon

## Migration from Old Tests

### Replaced Files
- ❌ `test_suite.py` (410 lines) → ✅ Modular test modules
- ❌ `quick_test.sh` (102 lines) → ✅ `run_tests.py` (200 lines)
- ❌ `run_tests_improved.sh` (206 lines) → ✅ Integrated into `run_tests.py`
- ❌ `test_runner.sh` (66 lines) → ✅ Replaced by pytest

### Benefits
1. **90% less code** - From 784 lines to ~80 lines of test runner
2. **Better organization** - Clear separation of test types
3. **Easier debugging** - Isolated tests with clear error messages
4. **Consistent patterns** - Uniform approach across all tests
5. **Better maintainability** - Modular structure is easier to update

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd backend
          python3 -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          source venv/bin/activate
          python3 run_tests.py
```

## Best Practices

### Writing Tests
1. **Use descriptive test names** - Clear what is being tested
2. **Test one thing at a time** - Single assertion per test
3. **Use fixtures for setup** - Reusable test data
4. **Mock external dependencies** - Isolate unit tests
5. **Clean up after tests** - Use pytest fixtures for cleanup

### Test Organization
1. **Group related tests** - Use test classes
2. **Use markers** - Categorize tests (unit, integration, slow)
3. **Keep tests focused** - One module per component
4. **Document complex tests** - Add docstrings for clarity

## Troubleshooting

### Test Failures
1. Check the test output for specific error messages
2. Verify environment setup (Python version, dependencies)
3. Ensure you're running from the correct directory
4. Check file permissions for database operations

### Performance Issues
1. Use `-m unit` to run only fast unit tests
2. Skip Docker tests if not needed: `-m "not docker"`
3. Use `--tb=short` for shorter tracebacks

### Environment Issues
1. Recreate virtual environment: `rm -rf venv && python3 -m venv venv`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python3 --version` 