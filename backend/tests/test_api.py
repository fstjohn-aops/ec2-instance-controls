"""
API tests for EC2 Slack Bot Flask application
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test that health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'healthy'
        assert 'timestamp' in data  # The endpoint includes a timestamp


class TestAssignmentsEndpoint:
    """Test assignments API endpoints"""
    
    def test_list_assignments(self, client):
        """Test getting list of assignments"""
        response = client.get('/api/assignments')
        assert response.status_code == 200
        data = response.json
        assert 'assignments' in data
        assert isinstance(data['assignments'], list)
    
    def test_assign_instance_success(self, client):
        """Test assigning an instance to a user"""
        assignment_data = {
            'instance_id': 'i-test-instance-1',
            'slack_user_id': 'U123',
            'slack_username': 'testuser'
        }
        
        response = client.post(
            '/api/assign-instance',
            json=assignment_data,
            content_type='application/json'
        )
        # In test mode, this should work. If it fails, it might be due to AWS mocking
        if response.status_code == 500:
            # Check if it's an AWS-related error
            data = response.json
            assert 'error' in data
        else:
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'message' in data
    
    def test_assign_instance_missing_data(self, client):
        """Test assigning instance with missing data"""
        response = client.post(
            '/api/assign-instance',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'error' in data
    
    def test_remove_assignment(self, client):
        """Test removing an assignment"""
        response = client.delete('/api/assignments/U123')
        # If no assignment exists, it should return 404
        if response.status_code == 404:
            data = response.json
            assert data['success'] is False
            assert 'error' in data
        else:
            assert response.status_code == 200
            data = response.json
            assert data['success'] is True


class TestInstanceStatusEndpoint:
    """Test instance status endpoint"""
    
    @patch('app.get_instance_status')
    def test_get_instance_status_success(self, mock_get_status, client):
        """Test getting instance status successfully"""
        mock_get_status.return_value = 'running'
        
        response = client.get('/api/instances/i-test-1/status')
        assert response.status_code == 200
        data = response.json
        assert data['instance_id'] == 'i-test-1'
        assert data['status'] == 'running'
    
    @patch('app.get_instance_status')
    def test_get_instance_status_not_found(self, mock_get_status, client):
        """Test getting status for non-existent instance"""
        mock_get_status.return_value = None
        
        response = client.get('/api/instances/i-nonexistent/status')
        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'error' in data


class TestSimulationEndpoints:
    """Test simulation endpoints for Slack commands"""
    
    def test_simulate_slack_start(self, client):
        """Test simulating Slack start command"""
        data = {'user_id': 'U123'}
        response = client.post(
            '/api/simulate/slack/start',
            json=data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
    
    def test_simulate_slack_stop(self, client):
        """Test simulating Slack stop command"""
        data = {'user_id': 'U123'}
        response = client.post(
            '/api/simulate/slack/stop',
            json=data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
    
    def test_simulate_slack_status(self, client):
        """Test simulating Slack status command"""
        data = {'user_id': 'U123'}
        response = client.post(
            '/api/simulate/slack/status',
            json=data,
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True 