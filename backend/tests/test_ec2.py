"""
EC2 operations tests for EC2 Slack Bot
"""
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from app import get_instance_status, start_instance, stop_instance


class TestEC2Operations:
    """Test EC2 operations"""
    
    @patch('app.ec2_client')
    def test_get_instance_status_success(self, mock_ec2_client):
        """Test getting instance status successfully"""
        # Mock successful response
        mock_response = {
            'Reservations': [{
                'Instances': [{
                    'State': {'Name': 'running'}
                }]
            }]
        }
        mock_ec2_client.describe_instances.return_value = mock_response
        
        result = get_instance_status('i-test-1')
        
        assert result == 'running'
        mock_ec2_client.describe_instances.assert_called_once_with(
            InstanceIds=['i-test-1']
        )
    
    @patch('app.ec2_client')
    def test_get_instance_status_not_found(self, mock_ec2_client):
        """Test getting status for non-existent instance"""
        # Mock empty response
        mock_response = {'Reservations': []}
        mock_ec2_client.describe_instances.return_value = mock_response
        
        result = get_instance_status('i-nonexistent')
        
        assert result is None
    
    @patch('app.ec2_client')
    def test_get_instance_status_error(self, mock_ec2_client):
        """Test getting instance status with AWS error"""
        # Mock AWS error
        mock_ec2_client.describe_instances.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidInstanceID.NotFound'}},
            operation_name='DescribeInstances'
        )
        
        result = get_instance_status('i-invalid')
        
        assert result is None
    
    @patch('app.ec2_client')
    def test_start_instance_success(self, mock_ec2_client):
        """Test starting instance successfully"""
        # Mock successful response
        mock_response = {
            'StartingInstances': [{
                'CurrentState': {'Name': 'pending'}
            }]
        }
        mock_ec2_client.start_instances.return_value = mock_response
        
        result = start_instance('i-test-1')
        
        assert result == 'pending'
        mock_ec2_client.start_instances.assert_called_once_with(
            InstanceIds=['i-test-1']
        )
    
    @patch('app.ec2_client')
    def test_start_instance_error(self, mock_ec2_client):
        """Test starting instance with AWS error"""
        # Mock AWS error
        mock_ec2_client.start_instances.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidInstanceID.NotFound'}},
            operation_name='StartInstances'
        )
        
        with pytest.raises(ClientError):
            start_instance('i-invalid')
    
    @patch('app.ec2_client')
    def test_stop_instance_success(self, mock_ec2_client):
        """Test stopping instance successfully"""
        # Mock successful response
        mock_response = {
            'StoppingInstances': [{
                'CurrentState': {'Name': 'stopping'}
            }]
        }
        mock_ec2_client.stop_instances.return_value = mock_response
        
        result = stop_instance('i-test-1')
        
        assert result == 'stopping'
        mock_ec2_client.stop_instances.assert_called_once_with(
            InstanceIds=['i-test-1']
        )
    
    @patch('app.ec2_client')
    def test_stop_instance_error(self, mock_ec2_client):
        """Test stopping instance with AWS error"""
        # Mock AWS error
        mock_ec2_client.stop_instances.side_effect = ClientError(
            error_response={'Error': {'Code': 'InvalidInstanceID.NotFound'}},
            operation_name='StopInstances'
        )
        
        with pytest.raises(ClientError):
            stop_instance('i-invalid')


class TestEC2TestMode:
    """Test EC2 operations in test mode"""
    
    @patch('app.TEST_MODE', True)
    def test_get_instance_status_test_mode(self):
        """Test getting instance status in test mode"""
        # Test with known test instance
        result = get_instance_status('i-test-instance-1')
        assert result == 'stopped'
        
        # Test with unknown instance
        result = get_instance_status('i-unknown')
        assert result == 'unknown'
    
    @patch('app.TEST_MODE', True)
    def test_start_instance_test_mode(self):
        """Test starting instance in test mode"""
        # Test with known test instance
        result = start_instance('i-test-instance-1')
        assert result == 'running'
        
        # Test with unknown instance
        result = start_instance('i-unknown')
        assert result == 'unknown'
    
    @patch('app.TEST_MODE', True)
    def test_stop_instance_test_mode(self):
        """Test stopping instance in test mode"""
        # Test with known test instance
        result = stop_instance('i-test-instance-2')
        assert result == 'stopped'
        
        # Test with unknown instance
        result = stop_instance('i-unknown')
        assert result == 'unknown' 