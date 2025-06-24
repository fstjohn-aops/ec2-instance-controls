#!/usr/bin/env python3
"""
Simple tests for EC2 Instance Control Flask App
"""

import json
import tempfile
import os
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client"""
    # Use a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    # Set test environment
    os.environ['TEST_MODE'] = 'true'
    os.environ['DB_PATH'] = test_db_path
    
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    try:
        os.unlink(test_db_path)
    except:
        pass


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['test_mode'] is True


def test_list_instances(client):
    """Test listing instances"""
    response = client.get('/api/instances')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'instances' in data
    assert isinstance(data['instances'], list)
    
    # In test mode, should have 3 mock instances
    assert len(data['instances']) == 3


def test_get_instance_status(client):
    """Test getting instance status"""
    # Test existing instance
    response = client.get('/api/instances/i-test-1/status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['instance_id'] == 'i-test-1'
    assert data['status'] == 'running'
    
    # Test non-existing instance
    response = client.get('/api/instances/i-nonexistent/status')
    assert response.status_code == 404


def test_start_instance(client):
    """Test starting an instance"""
    response = client.post('/api/instances/i-test-2/start')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['instance_id'] == 'i-test-2'
    assert data['status'] == 'running'
    assert 'started successfully' in data['message']


def test_stop_instance(client):
    """Test stopping an instance"""
    response = client.post('/api/instances/i-test-1/stop')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['instance_id'] == 'i-test-1'
    assert data['status'] == 'stopped'
    assert 'stopped successfully' in data['message']


def test_list_assignments_empty(client):
    """Test listing assignments when empty"""
    response = client.get('/api/assignments')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'assignments' in data
    assert isinstance(data['assignments'], list)
    assert len(data['assignments']) == 0


def test_create_assignment(client):
    """Test creating an assignment"""
    assignment_data = {
        'instance_id': 'i-test-1',
        'user_id': 'user123',
        'username': 'testuser',
        'instance_name': 'Test Instance'
    }
    
    response = client.post(
        '/api/assignments',
        json=assignment_data,
        content_type='application/json'
    )
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'created for instance' in data['message']


def test_create_assignment_missing_fields(client):
    """Test creating assignment with missing fields"""
    assignment_data = {
        'instance_id': 'i-test-1'
        # Missing user_id and username
    }
    
    response = client.post(
        '/api/assignments',
        json=assignment_data,
        content_type='application/json'
    )
    assert response.status_code == 400
    
    data = response.get_json()
    assert 'error' in data


def test_delete_assignment(client):
    """Test deleting an assignment"""
    # First create an assignment
    assignment_data = {
        'instance_id': 'i-test-1',
        'user_id': 'user123',
        'username': 'testuser'
    }
    client.post('/api/assignments', json=assignment_data)
    
    # Then delete it
    response = client.delete('/api/assignments/user123')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'deleted for user' in data['message']


def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data['error'] == 'Not found'


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v']) 