# EC2 Slack Bot Testing Guide

This document explains how to run the test suite for the EC2 Slack Bot.

## Test Suites Available

### 1. Python Test Suite (`test_suite.py`)
A comprehensive Python-based test suite that can run both locally and in containers.

**Features:**
- Environment detection (Docker, Python, dependencies)
- Database testing
- API endpoint testing
- Simulation endpoint testing
- Container testing (if Docker available)
- Local Flask app testing

**Usage:**
```bash
python3 test_suite.py
```

### 2. Improved Shell Test Suite (`run_tests_improved.sh`)
An improved version of the original shell script that handles missing Docker gracefully.

**Features:**
- Automatic environment detection
- Virtual environment setup
- Dependency installation
- Graceful fallback when Docker is not available
- Comprehensive error reporting

**Usage:**
```bash
./run_tests_improved.sh
```

### 3. Simple Test Runner (`test_runner.sh`)
A simple runner that tries all available test suites.

**Usage:**
```bash
./test_runner.sh
```

## Prerequisites

### Required
- Python 3.8+
- pip3

### Optional
- Docker and Docker Compose (for container testing)

## Setup

### 1. Environment Setup
Copy the template environment file and configure it:
```bash
cp env.template .env
```

Edit `.env` with your actual configuration:
```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Test Configuration
TEST_MODE=true
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

### Quick Start
For the easiest testing experience, use the simple test runner:
```bash
./test_runner.sh
```

### Manual Testing

#### 1. Python Test Suite (Recommended)
```bash
python3 test_suite.py
```

#### 2. Improved Shell Test Suite
```bash
./run_tests_improved.sh
```

## Test Phases

### Phase 1: Environment Setup
- Python version check
- Environment file setup
- Docker availability check
- Virtual environment setup

### Phase 2: Database Tests
- SQLite database creation
- Table creation
- Test data insertion
- Database operations

### Phase 3: Local Application Tests
- Flask app startup
- Health endpoint testing
- API endpoint testing
- Simulation endpoint testing

### Phase 4: Container Tests (if Docker available)
- Docker container build
- Container startup
- Health checks
- API testing in container

## Troubleshooting

### Common Issues

#### 1. Docker Not Available
**Problem:** Tests fail because Docker is not installed
**Solution:** Use the Python test suite or improved shell test suite

#### 2. Missing Dependencies
**Problem:** Import errors when running tests
**Solution:** Install dependencies with `pip install -r requirements.txt`

#### 3. Environment Variables Not Set
**Problem:** Tests fail due to missing environment variables
**Solution:** Copy `env.template` to `.env` and configure it

#### 4. Port Already in Use
**Problem:** Port 5000 is already in use
**Solution:** Stop other services using port 5000 or modify the port in the configuration

### Debug Mode
To run tests with more verbose output:
```bash
# Python test suite with debug
python3 -u test_suite.py

# Shell tests with debug
bash -x ./run_tests_improved.sh
```

## Test Results

### Success Indicators
- ✅ All environment checks pass
- ✅ Database operations work
- ✅ API endpoints respond correctly
- ✅ Simulation endpoints work
- ✅ Container tests pass (if Docker available)

### Next Steps After Successful Tests
1. Configure real Slack credentials in `.env`
2. Configure real AWS credentials
3. Deploy to production

## Production Deployment

After tests pass, you can deploy to production:

### With Docker
```bash
docker-compose up -d
```

### Without Docker
```bash
# Activate virtual environment
source venv/bin/activate

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the test output for specific error messages
3. Ensure all prerequisites are met
4. Verify environment configuration 