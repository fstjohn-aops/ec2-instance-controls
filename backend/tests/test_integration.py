"""
Integration tests for EC2 Slack Bot
"""
import pytest
import requests
import time
import subprocess
import os
from unittest.mock import patch


class TestIntegrationFlow:
    """Test complete integration flows"""
    
    @pytest.fixture
    def running_app(self):
        """Start the Flask app for integration testing"""
        # Set test environment
        env = os.environ.copy()
        env.update({
            'TEST_MODE': 'true',
            'FLASK_ENV': 'testing',
            'FLASK_DEBUG': 'false'
        })
        
        # Start app
        process = subprocess.Popen(
            ['python3', 'app.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    def test_complete_assignment_flow(self, running_app):
        """Test complete flow: assign instance -> check status -> start/stop"""
        base_url = "http://localhost:5000"
        
        # Step 1: Assign instance to user
        assignment_data = {
            'instance_id': 'i-test-instance-1',
            'slack_user_id': 'U123',
            'slack_username': 'testuser'
        }
        
        response = requests.post(
            f"{base_url}/api/assign-instance",
            json=assignment_data,
            timeout=10
        )
        assert response.status_code == 200
        
        # Step 2: Check instance status
        response = requests.get(
            f"{base_url}/api/instances/i-test-instance-1/status",
            timeout=10
        )
        assert response.status_code == 200
        data = response.json
        assert data['instance_id'] == 'i-test-instance-1'
        assert 'status' in data
        
        # Step 3: Simulate Slack start command
        response = requests.post(
            f"{base_url}/api/simulate/slack/start",
            json={'user_id': 'U123'},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        
        # Step 4: Simulate Slack stop command
        response = requests.post(
            f"{base_url}/api/simulate/slack/stop",
            json={'user_id': 'U123'},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
    
    def test_health_check_integration(self, running_app):
        """Test health check endpoint"""
        response = requests.get("http://localhost:5000/health", timeout=10)
        assert response.status_code == 200
        assert response.json == {'status': 'healthy'}
    
    def test_assignments_list_integration(self, running_app):
        """Test assignments list endpoint"""
        response = requests.get("http://localhost:5000/api/assignments", timeout=10)
        assert response.status_code == 200
        data = response.json
        assert 'assignments' in data
        assert isinstance(data['assignments'], list)


class TestErrorHandling:
    """Test error handling in integration scenarios"""
    
    @pytest.fixture
    def running_app(self):
        """Start the Flask app for integration testing"""
        env = os.environ.copy()
        env.update({
            'TEST_MODE': 'true',
            'FLASK_ENV': 'testing',
            'FLASK_DEBUG': 'false'
        })
        
        process = subprocess.Popen(
            ['python3', 'app.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(3)
        yield process
        process.terminate()
        process.wait()
    
    def test_invalid_assignment_data(self, running_app):
        """Test handling of invalid assignment data"""
        response = requests.post(
            "http://localhost:5000/api/assign-instance",
            json={},  # Missing required fields
            timeout=10
        )
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'error' in data
    
    def test_nonexistent_instance_status(self, running_app):
        """Test handling of non-existent instance"""
        response = requests.get(
            "http://localhost:5000/api/instances/i-nonexistent/status",
            timeout=10
        )
        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'error' in data
    
    def test_unauthorized_user_operations(self, running_app):
        """Test operations by unauthorized users"""
        # Try to start instance for user without assignment
        response = requests.post(
            "http://localhost:5000/api/simulate/slack/start",
            json={'user_id': 'U999'},  # User without assignment
            timeout=10
        )
        assert response.status_code == 200
        data = response.json
        # Should return success but with appropriate message
        assert data['success'] is True 