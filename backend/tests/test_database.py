"""
Database tests for EC2 Slack Bot
"""
import pytest
import sqlite3
import os
from datetime import datetime
from app import (
    init_db, 
    get_instance_for_user, 
    get_users_for_instance,
    create_instance_user_mapping,
    can_user_control_instance
)


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_init_db(self, test_db_path):
        """Test database initialization"""
        # Set up test environment
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Initialize database
        init_db()
        
        # Verify database was created
        assert os.path.exists(test_db_path)
        
        # Verify table structure
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instance_users'")
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'instance_users'
    
    def test_create_instance_user_mapping(self, test_db_path):
        """Test creating instance-user mapping"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Create mapping
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U123',
            slack_username='testuser'
        )
        
        # Verify mapping was created
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT instance_id, instance_name, slack_user_id, slack_username 
            FROM instance_users 
            WHERE instance_id = ?
        ''', ('i-test-1',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'i-test-1'
        assert result[1] == 'Test Instance'
        assert result[2] == 'U123'
        assert result[3] == 'testuser'
    
    def test_get_instance_for_user(self, test_db_path):
        """Test getting instance for a user"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Create test data
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U123',
            slack_username='testuser'
        )
        
        # Get instance for user
        result = get_instance_for_user('U123')
        
        assert result is not None
        assert result[0] == 'i-test-1'
        assert result[1] == 'Test Instance'
    
    def test_get_instance_for_nonexistent_user(self, test_db_path):
        """Test getting instance for non-existent user"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        result = get_instance_for_user('U999')
        assert result is None
    
    def test_get_users_for_instance(self, test_db_path):
        """Test getting users for an instance"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Create test data
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U123',
            slack_username='user1'
        )
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U456',
            slack_username='user2'
        )
        
        # Get users for instance
        results = get_users_for_instance('i-test-1')
        
        assert len(results) == 2
        user_ids = [result[0] for result in results]
        usernames = [result[1] for result in results]
        
        assert 'U123' in user_ids
        assert 'U456' in user_ids
        assert 'user1' in usernames
        assert 'user2' in usernames
    
    def test_can_user_control_instance(self, test_db_path):
        """Test checking if user can control instance"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Create test data
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U123',
            slack_username='testuser'
        )
        
        # Test authorized user
        assert can_user_control_instance('U123', 'i-test-1') is True
        
        # Test unauthorized user
        assert can_user_control_instance('U999', 'i-test-1') is False
        
        # Test non-existent instance
        assert can_user_control_instance('U123', 'i-nonexistent') is False
    
    def test_update_existing_mapping(self, test_db_path):
        """Test updating existing instance-user mapping"""
        os.environ['TEST_DB_PATH'] = test_db_path
        
        # Create initial mapping
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Test Instance',
            slack_user_id='U123',
            slack_username='olduser'
        )
        
        # Update mapping
        create_instance_user_mapping(
            instance_id='i-test-1',
            instance_name='Updated Instance',
            slack_user_id='U123',
            slack_username='newuser'
        )
        
        # Verify update
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT instance_name, slack_username 
            FROM instance_users 
            WHERE instance_id = ?
        ''', ('i-test-1',))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'Updated Instance'
        assert result[1] == 'newuser' 