import pytest
from unittest.mock import Mock, patch
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert data['service'] == 'ec2-instance-controls'

def test_health_endpoint_post_method_not_allowed(client):
    """Test that POST method is not allowed on health endpoint"""
    response = client.post('/health')
    assert response.status_code == 405  # Method Not Allowed

def test_instances_endpoint_missing_params(client):
    """Test instances endpoint with missing parameters"""
    response = client.post('/instances')
    assert response.status_code == 200  # Flask returns 200 even for missing params
    # No authentication check anymore, so it should work without user_id

def test_ec2_power_endpoint_missing_params(client):
    """Test EC2 power endpoint with missing parameters"""
    response = client.post('/ec2/power')
    assert response.status_code == 200
    # No authentication check anymore, so it should work without user_id

def test_ec2_schedule_endpoint_missing_params(client):
    """Test EC2 schedule endpoint with missing parameters"""
    response = client.post('/ec2-schedule')
    assert response.status_code == 200
    # No authentication check anymore, so it should work without user_id

def test_ec2_power_state_endpoint_same_as_power(client):
    """Test that ec2-power-state endpoint works the same as ec2/power"""
    # Both endpoints should behave identically
    response1 = client.post('/ec2/power')
    response2 = client.post('/ec2-power-state')
    
    assert response1.status_code == response2.status_code
    assert response1.get_data(as_text=True) == response2.get_data(as_text=True)

def test_instances_endpoint_with_params(client):
    """Test instances endpoint with valid parameters"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances:
        mock_get_instances.return_value = []
        
        response = client.post('/instances', data={
            'user_id': 'U08QYU6AX0V',
            'user_name': 'testuser'
        })
        
        assert response.status_code == 200
        assert "No instances found" in response.get_data(as_text=True)

def test_ec2_power_endpoint_with_params(client):
    """Test EC2 power endpoint with valid parameters"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = None
        
        response = client.post('/ec2/power', data={
            'user_id': 'U08QYU6AX0V',
            'text': 'invalid-instance'
        })
        
        assert response.status_code == 200
        assert "Instance `invalid-instance` not found" in response.get_data(as_text=True)

def test_ec2_schedule_endpoint_with_params(client):
    """Test EC2 schedule endpoint with valid parameters"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = None
        
        response = client.post('/ec2-schedule', data={
            'user_id': 'U08QYU6AX0V',
            'text': 'invalid-instance'
        })
        
        assert response.status_code == 200
        assert "Instance `invalid-instance` not found" in response.get_data(as_text=True)

def test_search_endpoint_with_params(client):
    """Test search endpoint with valid parameters"""
    with patch('src.handlers.fuzzy_search_instances') as mock_search:
        mock_search.return_value = [
            {
                'InstanceId': 'i-1234567890abcdef0',
                'Name': 'test-instance',
                'State': 'running'
            }
        ]
        
        response = client.post('/search', data={
            'user_id': 'U08QYU6AX0V',
            'user_name': 'testuser',
            'text': 'test'
        })
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert "Found 1 instance(s) matching 'test':" in response_text
        assert "test-instance" in response_text

def test_search_endpoint_empty_term(client):
    """Test search endpoint with empty search term"""
    response = client.post('/search', data={
        'user_id': 'U08QYU6AX0V',
        'user_name': 'testuser',
        'text': ''
    })
    
    assert response.status_code == 200
    assert "Please provide a search term" in response.get_data(as_text=True) 