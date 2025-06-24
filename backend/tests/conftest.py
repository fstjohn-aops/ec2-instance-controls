"""
Pytest configuration and common fixtures for EC2 Slack Bot tests
"""
import os
import pytest
import tempfile
import sqlite3
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="session")
def test_db_path(test_data_dir):
    """Create a test database path"""
    return os.path.join(test_data_dir, "test_ec2_instances.db")


@pytest.fixture(scope="session")
def test_db(test_db_path):
    """Create and initialize test database"""
    # Create database
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instance_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id TEXT UNIQUE NOT NULL,
            instance_name TEXT,
            slack_user_id TEXT NOT NULL,
            slack_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test data
    test_data = [
        ('i-test-1', 'Test Instance 1', 'U123', 'alice'),
        ('i-test-2', 'Test Instance 2', 'U456', 'bob'),
    ]
    
    for instance_id, instance_name, slack_user_id, slack_username in test_data:
        cursor.execute('''
            INSERT OR REPLACE INTO instance_users 
            (instance_id, instance_name, slack_user_id, slack_username)
            VALUES (?, ?, ?, ?)
        ''', (instance_id, instance_name, slack_user_id, slack_username))
    
    conn.commit()
    conn.close()
    
    return test_db_path


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    original_env = os.environ.copy()
    
    # Set test environment
    test_env_vars = {
        'TEST_MODE': 'true',
        'FLASK_ENV': 'testing',
        'FLASK_DEBUG': 'false',
        'SLACK_BOT_TOKEN': 'xoxb-test-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret',
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
        'AWS_REGION': 'us-east-1',
    }
    
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    yield test_env_vars
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env) 