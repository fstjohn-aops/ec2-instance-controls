import pytest
from unittest.mock import Mock, patch
from flask import Flask
from datetime import timedelta
from src.handlers import handle_ec2_power, handle_list_instances, handle_ec2_schedule, handle_ec2_disable_schedule, handle_fuzzy_search, handle_ec2_stakeholder
from src.schedule import parse_time, format_schedule_display
from src.disable_schedule import parse_hours, format_disable_schedule_display

# Create a test Flask app
app = Flask(__name__)

# Instance list tests
def test_list_instances_with_instances():
    """Test listing instances with valid instances"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances, \
         patch('src.handlers.get_instance_state') as mock_get_state, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        
        mock_get_instances.return_value = ['i-1234567890abcdef0', 'i-0987654321fedcba0']
        mock_get_state.side_effect = ['running', 'stopped']
        mock_get_name.side_effect = ['test-instance-1', 'test-instance-2']
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "Controllable instances in AWS region:" in result
        assert "test-instance-1" in result
        assert "test-instance-2" in result
        assert "running" in result
        assert "stopped" in result

def test_list_instances_no_instances():
    """Test listing instances when no instances exist in the region"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances:
        mock_get_instances.return_value = []
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "No controllable instances found" in result

def test_list_instances_instance_state_unknown():
    """Test listing instances when instance state is unknown"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances, \
         patch('src.handlers.get_instance_state') as mock_get_state, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        
        mock_get_instances.return_value = ['i-0df9c53001c5c837d']
        mock_get_state.return_value = None
        mock_get_name.return_value = 'test-instance'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "unknown state" in result

# EC2 Power tests
def test_ec2_power_check_status():
    """Test EC2 power status check"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_power(request)
            assert "test-instance" in result
            assert "running" in result

def test_ec2_power_check_status_no_name():
    """Test EC2 power status check when instance has no name"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_get_name.return_value = None
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_power(request)
            assert "i-0df9c53001c5c837d" in result
            assert "running" in result

def test_ec2_power_start_instance():
    """Test EC2 power start instance"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.start_instance') as mock_start, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_start.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "Set `test-instance`" in result.json['text']
            assert "to on" in result.json['text']

def test_ec2_power_stop_instance():
    """Test EC2 power stop instance"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.stop_instance') as mock_stop, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_stop.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d off'}
            
            result = handle_ec2_power(request)
            assert "Set `test-instance`" in result.json['text']
            assert "to off" in result.json['text']

def test_ec2_power_restart_instance():
    """Test EC2 power restart instance"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.restart_instance') as mock_restart, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_restart.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d restart'}
            
            result = handle_ec2_power(request)
            assert "Set `test-instance`" in result.json['text']
            assert "to restart" in result.json['text']

def test_ec2_power_restart_stopped_instance():
    """Test EC2 power restart instance that is currently stopped"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.restart_instance') as mock_restart, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_restart.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d restart'}
            
            result = handle_ec2_power(request)
            assert "Cannot restart `test-instance`" in result.json['text']
            assert "instance is currently stopped" in result.json['text']

def test_ec2_power_restart_stopped_instance_no_name():
    """Test EC2 power restart instance that is currently stopped and has no name"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.restart_instance') as mock_restart, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_restart.return_value = False
            mock_get_name.return_value = None
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d restart'}
            
            result = handle_ec2_power(request)
            assert "Cannot restart `i-0df9c53001c5c837d`" in result.json['text']
            assert "instance is currently stopped" in result.json['text']

# AWS Client function tests
def test_restart_instance_stopped():
    """Test restart_instance when instance is stopped"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state, \
         patch('src.aws_client.get_instance_name') as mock_get_name:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'stopped'
        mock_get_name.return_value = 'test-instance'
        
        from src.aws_client import restart_instance
        
        result = restart_instance('i-0df9c53001c5c837d')
        assert result is False

def test_restart_instance_running():
    """Test restart_instance when instance is running"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state, \
         patch('src.aws_client._get_ec2_client') as mock_client, \
         patch('src.aws_client.get_instance_name') as mock_get_name:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'running'
        mock_get_name.return_value = 'test-instance'
        
        # Mock the EC2 client response
        mock_ec2_client = Mock()
        mock_ec2_client.reboot_instances.return_value = {
            'StartingInstances': [{
                'PreviousState': {'Name': 'running'},
                'CurrentState': {'Name': 'running'}
            }]
        }
        mock_client.return_value = mock_ec2_client
        
        from src.aws_client import restart_instance
        
        result = restart_instance('i-0df9c53001c5c837d')
        assert result is True
        mock_ec2_client.reboot_instances.assert_called_once_with(InstanceIds=['i-0df9c53001c5c837d'])

def test_restart_instance_not_controllable():
    """Test restart_instance when instance cannot be controlled"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control:
        mock_can_control.return_value = False
        
        from src.aws_client import restart_instance
        
        result = restart_instance('i-0df9c53001c5c837d')
        assert result is False

# New tests for comprehensive error handling
def test_start_instance_already_running():
    """Test start_instance when instance is already running"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'running'
        
        from src.aws_client import start_instance
        
        result = start_instance('i-0df9c53001c5c837d')
        assert result is False

def test_start_instance_pending():
    """Test start_instance when instance is pending"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'pending'
        
        from src.aws_client import start_instance
        
        result = start_instance('i-0df9c53001c5c837d')
        assert result is False

def test_start_instance_stopping():
    """Test start_instance when instance is stopping"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'stopping'
        
        from src.aws_client import start_instance
        
        result = start_instance('i-0df9c53001c5c837d')
        assert result is False

def test_stop_instance_already_stopped():
    """Test stop_instance when instance is already stopped"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'stopped'
        
        from src.aws_client import stop_instance
        
        result = stop_instance('i-0df9c53001c5c837d')
        assert result is False

def test_stop_instance_stopping():
    """Test stop_instance when instance is already stopping"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'stopping'
        
        from src.aws_client import stop_instance
        
        result = stop_instance('i-0df9c53001c5c837d')
        assert result is False

def test_stop_instance_pending():
    """Test stop_instance when instance is pending"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'pending'
        
        from src.aws_client import stop_instance
        
        result = stop_instance('i-0df9c53001c5c837d')
        assert result is False

def test_restart_instance_pending():
    """Test restart_instance when instance is pending"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'pending'
        
        from src.aws_client import restart_instance
        
        result = restart_instance('i-0df9c53001c5c837d')
        assert result is False

def test_restart_instance_stopping():
    """Test restart_instance when instance is stopping"""
    with patch('src.aws_client.can_control_instance_by_id') as mock_can_control, \
         patch('src.aws_client.get_instance_state') as mock_get_state:
        
        mock_can_control.return_value = True
        mock_get_state.return_value = 'stopping'
        
        from src.aws_client import restart_instance
        
        result = restart_instance('i-0df9c53001c5c837d')
        assert result is False

# Handler tests for user-friendly error messages
def test_ec2_power_start_already_running():
    """Test EC2 power start when instance is already running"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.start_instance') as mock_start, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_start.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "already running" in result.json['text']

def test_ec2_power_start_pending():
    """Test EC2 power start when instance is pending"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.start_instance') as mock_start, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'pending'
            mock_start.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "already starting" in result.json['text']

def test_ec2_power_stop_already_stopped():
    """Test EC2 power stop when instance is already stopped"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.stop_instance') as mock_stop, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_stop.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d off'}
            
            result = handle_ec2_power(request)
            assert "already stopped" in result.json['text']

def test_ec2_power_restart_pending():
    """Test EC2 power restart when instance is pending"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.restart_instance') as mock_restart, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'pending'
            mock_restart.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d restart'}
            
            result = handle_ec2_power(request)
            assert "currently starting" in result.json['text']

def test_ec2_power_access_denied():
    """Test EC2 power access denied for unauthorized user - now any authenticated user can access"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.start_instance') as mock_start, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_start.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U123456789', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "Set `test-instance`" in result.json['text']
            assert "to on" in result.json['text']

def test_ec2_power_instance_not_found():
    """Test EC2 power with non-existent instance"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = None
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-nonexistent on'}
        
        result = handle_ec2_power(request)
        assert "Instance `i-nonexistent` not found" in result

def test_ec2_power_valid():
    """Test EC2 power with valid input"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_state') as mock_get_state, \
             patch('src.handlers.start_instance') as mock_start, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_start.return_value = True
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "Set `i-0df9c53001c5c837d`" in result.json['text']
            assert "to on" in result.json['text']

def test_ec2_power_invalid_format():
    """Test EC2 power with invalid format"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = None
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'invalid'}
        
        result = handle_ec2_power(request)
        assert "Instance `invalid` not found" in result

def test_ec2_power_invalid_state():
    """Test EC2 power with invalid power state"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d maybe'}
        
        result = handle_ec2_power(request)
        assert "must be 'on', 'off', or 'restart'" in result

def test_ec2_power_usage_message():
    """Test EC2 power with too many arguments"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on extra'}
    
    result = handle_ec2_power(request)
    assert "Usage:" in result

def test_ec2_power_empty_text():
    """Test EC2 power with empty text"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': ''}
    
    result = handle_ec2_power(request)
    assert "Usage:" in result

def test_ec2_power_missing_text():
    """Test EC2 power with missing text"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V'}
    
    result = handle_ec2_power(request)
    assert "Usage:" in result

def test_ec2_power_instance_not_controllable():
    """Test EC2 power with instance that cannot be controlled"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = False
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
            
            result = handle_ec2_power(request)
            assert "cannot be controlled by this service" in result
            assert "EC2ControlsEnabled" in result

# Schedule tests
def test_ec2_schedule_get_no_schedule():
    """Test getting schedule when none exists"""
    with app.app_context():
        with patch('src.handlers.get_schedule') as mock_get_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_get_schedule.return_value = None
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_schedule(request)
            assert "No schedule set" in result

def test_ec2_schedule_get_with_schedule():
    """Test getting schedule when one exists"""
    with app.app_context():
        with patch('src.handlers.get_schedule') as mock_get_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_get_schedule.return_value = {
                'start_time': '09:00',
                'stop_time': '17:00'
            }
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_schedule(request)
            assert "9:00 AM to 5:00 PM" in result

def test_ec2_schedule_set_valid():
    """Test setting a valid schedule"""
    with app.app_context():
        with patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_set_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule set for" in result.json['text']

def test_ec2_schedule_set_invalid_start_time():
    """Test setting schedule with invalid start time"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d invalid to 5pm'}
        
        result = handle_ec2_schedule(request)
        assert "Invalid start time" in result

def test_ec2_schedule_set_invalid_stop_time():
    """Test setting schedule with invalid stop time"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to invalid'}
        
        result = handle_ec2_schedule(request)
        assert "Invalid stop time" in result

def test_ec2_schedule_set_invalid_order():
    """Test setting schedule with end time before start time (cross-midnight)"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 5am to 4am'}
        
        result = handle_ec2_schedule(request)
        # This should be rejected as cross-midnight schedules are not supported
        assert "Invalid schedule: start time (5am) must be before end time (4am)" in result
        assert "Cross-midnight schedules are not supported" in result

def test_ec2_schedule_set_same_time():
    """Test setting schedule with same start and end time"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 9am'}
        
        result = handle_ec2_schedule(request)
        assert "Invalid schedule: start time (9am) must be before end time (9am)" in result
        assert "Cross-midnight schedules are not supported" in result

def test_ec2_schedule_set_across_midnight():
    """Test setting schedule that spans midnight (should be rejected)"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 11pm to 7am'}
        
        result = handle_ec2_schedule(request)
        assert "Invalid schedule: start time (11pm) must be before end time (7am)" in result
        assert "Cross-midnight schedules are not supported" in result

def test_ec2_schedule_set_failed():
    """Test setting schedule when it fails"""
    with app.app_context():
        with patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_set_schedule.return_value = False
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
            
            result = handle_ec2_schedule(request)
            assert "Failed to set schedule" in result

def test_ec2_schedule_access_denied():
    """Test schedule access denied for unauthorized user - now any authenticated user can access"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_schedule') as mock_get_schedule, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_schedule.return_value = None
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U123456789', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule for `test-instance`" in result
            assert "No schedule set" in result

def test_ec2_schedule_instance_not_found():
    """Test schedule with non-existent instance"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
        mock_resolve.return_value = None
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-nonexistent 9am to 5pm'}
        
        result = handle_ec2_schedule(request)
        assert "Instance `i-nonexistent` not found" in result

def test_ec2_schedule_usage_message():
    """Test schedule with invalid format"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d extra argument'}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_missing_to():
    """Test schedule without 'to' keyword"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am 5pm'}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_to_at_beginning():
    """Test schedule with 'to' at beginning"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d to 5pm'}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_to_at_end():
    """Test schedule with 'to' at end"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to'}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_clear():
    """Test clearing a schedule"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d clear'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_reset():
    """Test resetting a schedule"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d reset'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_unset():
    """Test unsetting a schedule"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d unset'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_clear_failed():
    """Test clearing a schedule when it fails"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            mock_delete_schedule.return_value = False
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d clear'}
            
            result = handle_ec2_schedule(request)
            assert "Failed to clear schedule" in result

def test_ec2_schedule_invalid_command():
    """Test schedule with invalid command"""
    with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        mock_resolve.return_value = 'i-0df9c53001c5c837d'
        mock_get_name.return_value = 'i-0df9c53001c5c837d'
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d invalid'}
        
        result = handle_ec2_schedule(request)
        assert "Usage:" in result

def test_ec2_schedule_empty_text():
    """Test schedule with empty text"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': ''}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_missing_text():
    """Test schedule with missing text"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V'}
    
    result = handle_ec2_schedule(request)
    assert "Usage:" in result

def test_ec2_schedule_case_insensitive_clear():
    """Test schedule clear commands are case insensitive"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            # Test uppercase
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d CLEAR'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']
            
            # Test mixed case
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d Clear'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_complex_time_formats():
    """Test schedule with complex time formats"""
    with app.app_context():
        with patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_set_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            
            # Test various time formats
            time_formats = [
                '9:30am to 5:30pm',
                '17:00 to 09:00',
                '12:00am to 11:59pm'
            ]
            
            for time_format in time_formats:
                request = Mock()
                request.form = {'user_id': 'U08QYU6AX0V', 'text': f'i-0df9c53001c5c837d {time_format}'}
                
                result = handle_ec2_schedule(request)
                result_text = result.json['text'] if hasattr(result, 'json') else str(result)
                # Should either succeed or give a clear error message
                assert any(msg in result_text for msg in [
                    "Schedule set for", "Invalid start time", "Invalid stop time", "Invalid schedule: start time", "Usage:"
                ])

# Time parsing tests
def test_parse_time_5am():
    """Test parsing '5am'"""
    result = parse_time('5am')
    assert result.hour == 5
    assert result.minute == 0

def test_parse_time_5_00am():
    """Test parsing '5:00am'"""
    result = parse_time('5:00am')
    assert result.hour == 5
    assert result.minute == 0

def test_parse_time_5_00_am():
    """Test parsing '5:00 am'"""
    result = parse_time('5:00 am')
    assert result.hour == 5
    assert result.minute == 0

def test_parse_time_5_00_Am():
    """Test parsing '5:00 Am'"""
    result = parse_time('5:00 Am')
    assert result.hour == 5
    assert result.minute == 0

def test_parse_time_17_00():
    """Test parsing '17:00' (24-hour format)"""
    result = parse_time('17:00')
    assert result.hour == 17
    assert result.minute == 0

def test_parse_time_5_30pm():
    """Test parsing '5:30pm'"""
    result = parse_time('5:30pm')
    assert result.hour == 17
    assert result.minute == 30

def test_parse_time_invalid():
    """Test parsing invalid time"""
    result = parse_time('invalid')
    assert result is None

def test_parse_time_empty():
    """Test parsing empty time string"""
    result = parse_time('')
    assert result is None

def test_parse_time_whitespace():
    """Test parsing whitespace-only time string"""
    result = parse_time('   ')
    assert result is None

def test_parse_time_none():
    """Test parsing None time"""
    result = parse_time(None)
    assert result is None

def test_parse_time_invalid_hour():
    """Test parsing time with invalid hour"""
    result = parse_time('25:00')
    assert result is None

def test_parse_time_invalid_minute():
    """Test parsing time with invalid minute"""
    result = parse_time('9:60am')
    assert result is None

def test_parse_time_mixed_format():
    """Test parsing time with mixed 24-hour and AM/PM format"""
    result = parse_time('13:00am')
    assert result is None

def test_parse_time_12am():
    """Test parsing 12am (midnight)"""
    result = parse_time('12am')
    assert result.hour == 0
    assert result.minute == 0

def test_parse_time_12pm():
    """Test parsing 12pm (noon)"""
    result = parse_time('12pm')
    assert result.hour == 12
    assert result.minute == 0

def test_parse_time_12_30am():
    """Test parsing 12:30am (midnight + 30 minutes)"""
    result = parse_time('12:30am')
    assert result.hour == 0
    assert result.minute == 30

def test_parse_time_12_30pm():
    """Test parsing 12:30pm (noon + 30 minutes)"""
    result = parse_time('12:30pm')
    assert result.hour == 12
    assert result.minute == 30

# Schedule display tests
def test_format_schedule_display_no_schedule():
    """Test formatting display when no schedule exists"""
    result = format_schedule_display(None)
    assert result == "No schedule set"

def test_format_schedule_display_with_schedule():
    """Test formatting display with valid schedule"""
    schedule = {'start_time': '09:00', 'stop_time': '17:00'}
    result = format_schedule_display(schedule)
    assert result == "9:00 AM to 5:00 PM"

def test_format_schedule_display_midnight():
    """Test formatting display with midnight times"""
    schedule = {'start_time': '00:00', 'stop_time': '23:59'}
    result = format_schedule_display(schedule)
    assert result == "12:00 AM to 11:59 PM"

def test_fuzzy_search_with_results():
    """Test fuzzy search with matching instances"""
    with patch('src.handlers.fuzzy_search_instances') as mock_search:
        mock_search.return_value = [
            {
                'InstanceId': 'i-1234567890abcdef0',
                'Name': 'test-instance-1',
                'State': 'running'
            },
            {
                'InstanceId': 'i-0987654321fedcba0',
                'Name': 'test-instance-2',
                'State': 'stopped'
            }
        ]
        
        request = Mock()
        request.form = {
            'user_id': 'U08QYU6AX0V',
            'user_name': 'fstjohn',
            'text': 'test'
        }
        
        result = handle_fuzzy_search(request)
        assert "Found 2 controllable instance(s) matching 'test':" in result
        assert "test-instance-1" in result
        assert "test-instance-2" in result
        assert "running" in result
        assert "stopped" in result

def test_fuzzy_search_no_results():
    """Test fuzzy search when no instances match"""
    with patch('src.handlers.fuzzy_search_instances') as mock_search:
        mock_search.return_value = []
        
        request = Mock()
        request.form = {
            'user_id': 'U08QYU6AX0V',
            'user_name': 'fstjohn',
            'text': 'nonexistent'
        }
        
        result = handle_fuzzy_search(request)
        assert "No controllable instances found matching 'nonexistent'" in result
        assert "EC2ControlsEnabled" in result

def test_fuzzy_search_empty_term():
    """Test fuzzy search with empty search term"""
    with patch('src.handlers.fuzzy_search_instances') as mock_search:
        mock_search.return_value = []
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': ''}
        
        result = handle_fuzzy_search(request)
        assert "Please provide a search term" in result

def test_ec2_schedule_with_aws_tags():
    """Test that schedule functions work with EC2 tags"""
    with app.app_context():
        with patch('src.handlers.get_schedule') as mock_get_schedule, \
             patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            # Test getting schedule from EC2 tags
            mock_get_schedule.return_value = {
                'start_time': '09:00',
                'stop_time': '17:00'
            }
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_schedule(request)
            assert "9:00 AM to 5:00 PM" in result
            
            # Test setting schedule with EC2 tags
            mock_set_schedule.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 8am to 6pm'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule set for" in result.json['text']
            assert "8:00 AM to 6:00 PM" in result.json['text']
            
            # Test clearing schedule with EC2 tags
            mock_delete_schedule.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d clear'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_instance_not_controllable():
    """Test EC2 schedule with instance that cannot be controlled"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = False
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
            
            result = handle_ec2_schedule(request)
            assert "cannot be controlled by this service" in result
            assert "EC2ControlsEnabled" in result

def test_list_instances_only_controllable():
    """Test that list instances only shows controllable instances"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances, \
         patch('src.handlers.get_instance_state') as mock_get_state, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        
        mock_get_instances.return_value = ['i-1234567890abcdef0', 'i-0987654321fedcba0']
        mock_get_state.side_effect = ['running', 'stopped']
        mock_get_name.side_effect = ['test-instance-1', 'test-instance-2']
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "Controllable instances in AWS region:" in result
        assert "test-instance-1" in result
        assert "test-instance-2" in result

def test_list_instances_no_controllable():
    """Test list instances when no controllable instances exist"""
    with patch('src.handlers.get_all_region_instances') as mock_get_instances:
        mock_get_instances.return_value = []
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "No controllable instances found" in result
        assert "EC2ControlsEnabled" in result

# EC2 Disable Schedule tests
def test_ec2_disable_schedule_get_no_schedule():
    """Test EC2 disable schedule get when no schedule is set"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_disable_schedule') as mock_get_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_disable.return_value = None
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_disable_schedule(request)
            assert "test-instance" in result
            assert "No disable schedule set" in result

def test_ec2_disable_schedule_get_with_schedule():
    """Test EC2 disable schedule get when schedule is set"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_disable_schedule') as mock_get_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            from datetime import datetime, timezone, timedelta
            # Create a datetime in the future to avoid "expired" message
            now = datetime.now(timezone.utc)
            disable_until = now + timedelta(hours=2, minutes=30)
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_disable.return_value = disable_until
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_disable_schedule(request)
            assert "test-instance" in result
            # The exact time might vary slightly due to test execution time
            # so we check for the general format instead of exact values
            assert "Disabled for" in result
            assert "h" in result
            assert "m" in result

def test_ec2_disable_schedule_set_valid():
    """Test EC2 disable schedule set with valid hours"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.set_disable_schedule') as mock_set_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.parse_hours') as mock_parse_hours:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_set_disable.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            mock_parse_hours.return_value = 2
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 2h'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Disable schedule set for `test-instance`" in result.json['text']
            assert "for 2 hours" in result.json['text']

def test_ec2_disable_schedule_set_invalid_hours():
    """Test EC2 disable schedule set with invalid hours"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.parse_hours') as mock_parse_hours:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_parse_hours.return_value = None
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d invalid-hours'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Invalid hours format: invalid-hours" in result

def test_ec2_disable_schedule_set_failed():
    """Test EC2 disable schedule set when AWS operation fails"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.set_disable_schedule') as mock_set_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.parse_hours') as mock_parse_hours:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_set_disable.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            mock_parse_hours.return_value = 2
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 2h'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Failed to set disable schedule for `test-instance`" in result

def test_ec2_disable_schedule_access_denied():
    """Test EC2 disable schedule set when instance cannot be controlled"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.parse_hours') as mock_parse_hours:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = False
            mock_parse_hours.return_value = 2
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 2h'}
            
            result = handle_ec2_disable_schedule(request)
            assert "test-instance" in result
            assert "cannot be controlled by this service" in result
            assert "EC2ControlsEnabled" in result

def test_ec2_disable_schedule_instance_not_found():
    """Test EC2 disable schedule when instance is not found"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
            
            mock_resolve.return_value = None
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'nonexistent-instance'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Instance `nonexistent-instance` not found" in result

def test_ec2_disable_schedule_usage_message():
    """Test EC2 disable schedule usage message"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': ''}
        
        result = handle_ec2_disable_schedule(request)
        assert "Usage:" in result
        assert "cancel" in result

def test_ec2_disable_schedule_empty_text():
    """Test EC2 disable schedule with empty text"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': ''}
        
        result = handle_ec2_disable_schedule(request)
        assert "Usage:" in result

def test_ec2_disable_schedule_missing_text():
    """Test EC2 disable schedule with missing text"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V'}
        
        result = handle_ec2_disable_schedule(request)
        assert "Usage:" in result

def test_ec2_disable_schedule_cancel():
    """Test EC2 disable schedule cancel command"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.delete_disable_schedule') as mock_delete_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_delete_disable.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d cancel'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Disable schedule cancelled for `test-instance`" in result.json['text']

def test_ec2_disable_schedule_clear():
    """Test EC2 disable schedule clear command"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.delete_disable_schedule') as mock_delete_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_delete_disable.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d clear'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Disable schedule cancelled for `test-instance`" in result.json['text']

def test_ec2_disable_schedule_cancel_failed():
    """Test EC2 disable schedule cancel when AWS operation fails"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.delete_disable_schedule') as mock_delete_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_delete_disable.return_value = False
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d cancel'}
            
            result = handle_ec2_disable_schedule(request)
            assert "Failed to cancel disable schedule for `i-0df9c53001c5c837d`" in result

def test_ec2_disable_schedule_cancel_not_controllable():
    """Test EC2 disable schedule cancel when instance cannot be controlled"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = False
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d cancel'}
            
            result = handle_ec2_disable_schedule(request)
            assert "test-instance" in result
            assert "cannot be controlled by this service" in result
            assert "EC2ControlsEnabled" in result

def test_ec2_disable_schedule_case_insensitive_cancel():
    """Test EC2 disable schedule cancel with different case variations"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.delete_disable_schedule') as mock_delete_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control:
            
            mock_delete_disable.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            # Test different cancel command variations
            cancel_commands = ['CANCEL', 'Clear', 'RESET', 'Unset', 'NO', 'Remove', 'DELETE']
            
            for command in cancel_commands:
                request = Mock()
                request.form = {'user_id': 'U08QYU6AX0V', 'text': f'i-0df9c53001c5c837d {command}'}
                
                result = handle_ec2_disable_schedule(request)
                assert "Disable schedule cancelled for `test-instance`" in result.json['text']

def test_ec2_disable_schedule_various_hours_formats():
    """Test EC2 disable schedule with various hours formats"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.set_disable_schedule') as mock_set_disable, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.parse_hours') as mock_parse_hours:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_set_disable.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_can_control.return_value = True
            
            # Test various hours formats
            hours_formats = ['1h', '2h', '24h', '48h', '168h']
            
            for hours_str in hours_formats:
                hours = int(hours_str[:-1])
                mock_parse_hours.return_value = hours
                
                request = Mock()
                request.form = {'user_id': 'U08QYU6AX0V', 'text': f'i-0df9c53001c5c837d {hours_str}'}
                
                result = handle_ec2_disable_schedule(request)
                assert "Disable schedule set for `test-instance`" in result.json['text']
                assert f"for {hours} hours" in result.json['text']

# Disable Schedule Module tests
def test_parse_hours_valid():
    """Test parse_hours with valid hours string"""
    result = parse_hours('2h')
    assert result == 2

def test_parse_hours_invalid():
    """Test parse_hours with invalid hours string"""
    result = parse_hours('invalid-hours')
    assert result is None

def test_parse_hours_empty():
    """Test parse_hours with empty string"""
    result = parse_hours('')
    assert result is None

def test_parse_hours_none():
    """Test parse_hours with None"""
    result = parse_hours(None)
    assert result is None

def test_parse_hours_below_minimum():
    """Test parse_hours with value below minimum"""
    result = parse_hours('0h')
    assert result is None

def test_parse_hours_no_h_suffix():
    """Test parse_hours without 'h' suffix"""
    result = parse_hours('2')
    assert result is None

def test_parse_hours_invalid_number():
    """Test parse_hours with invalid number"""
    result = parse_hours('ah')
    assert result is None

def test_format_disable_schedule_display_no_schedule():
    """Test format_disable_schedule_display with no schedule"""
    result = format_disable_schedule_display(None)
    assert result == "No disable schedule set"

def test_format_disable_schedule_display_with_schedule():
    """Test formatting disable schedule display with a schedule"""
    from datetime import datetime, timezone
    # Create a datetime 2 hours in the future
    now = datetime.now(timezone.utc)
    disable_until = now + timedelta(hours=2)
    
    result = format_disable_schedule_display(disable_until)
    # The exact time might vary slightly due to test execution time
    # so we check for the general format instead of exact values
    assert "Disabled for" in result
    assert "h" in result

# EC2 Stakeholder tests
def test_ec2_stakeholder_claim_success():
    """Test successful EC2 stakeholder claim"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (True, "added")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are now a stakeholder for `test-instance`" in result
            assert "i-0df9c53001c5c837d" in result

def test_ec2_stakeholder_claim_default():
    """Test EC2 stakeholder claim with default action (no action specified)"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (True, "added")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are now a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_claim_success_no_name():
    """Test successful EC2 stakeholder claim when instance has no name"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = None
            mock_add_stakeholder.return_value = (True, "added")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are now a stakeholder for `i-0df9c53001c5c837d`" in result

def test_ec2_stakeholder_claim_already_stakeholder():
    """Test EC2 stakeholder claim when user is already a stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (True, "already_stakeholder")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are already a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_claim_max_limit_reached():
    """Test EC2 stakeholder claim when max stakeholders limit is reached"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (False, "max_limit_reached")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "Max stakeholders (10) reached for `test-instance`" in result

def test_ec2_stakeholder_remove_success():
    """Test successful EC2 stakeholder remove"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.remove_stakeholder') as mock_remove_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_remove_stakeholder.return_value = (True, "removed")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d remove'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are no longer a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_remove_not_stakeholder():
    """Test EC2 stakeholder remove when user is not a stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.remove_stakeholder') as mock_remove_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_remove_stakeholder.return_value = (True, "not_stakeholder")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d remove'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are not a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_remove_failed():
    """Test EC2 stakeholder remove when operation fails"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.remove_stakeholder') as mock_remove_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_remove_stakeholder.return_value = (False, "failed")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d remove'}
            
            result = handle_ec2_stakeholder(request)
            assert "Failed to remove stakeholder status for `test-instance`" in result

def test_ec2_stakeholder_check_is_stakeholder():
    """Test EC2 stakeholder check when user is a stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.is_user_stakeholder') as mock_is_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_is_stakeholder.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d check'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_check_not_stakeholder():
    """Test EC2 stakeholder check when user is not a stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.is_user_stakeholder') as mock_is_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_is_stakeholder.return_value = False
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d check'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are not a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_check_no_name():
    """Test EC2 stakeholder check when instance has no name"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.is_user_stakeholder') as mock_is_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = None
            mock_is_stakeholder.return_value = True
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d check'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are a stakeholder for `i-0df9c53001c5c837d`" in result

def test_ec2_stakeholder_instance_not_found():
    """Test EC2 stakeholder when instance is not found"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve:
            
            mock_resolve.return_value = None
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'nonexistent-instance claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "Instance `nonexistent-instance` not found" in result

def test_ec2_stakeholder_instance_not_controllable():
    """Test EC2 stakeholder when instance cannot be controlled"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = False
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "cannot be controlled by this service" in result
            assert "EC2ControlsEnabled" in result

def test_ec2_stakeholder_invalid_action():
    """Test EC2 stakeholder with invalid action"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d invalid'}
        
        result = handle_ec2_stakeholder(request)
        assert "Action must be 'claim', 'remove', or 'check'" in result

def test_ec2_stakeholder_invalid_format():
    """Test EC2 stakeholder with invalid format"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim extra-param'}
        
        result = handle_ec2_stakeholder(request)
        assert "Usage: <instance-id|instance-name> [claim|remove|check]" in result

def test_ec2_stakeholder_empty_text():
    """Test EC2 stakeholder with empty text"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': ''}
        
        result = handle_ec2_stakeholder(request)
        assert "Usage: <instance-id|instance-name> [claim|remove|check]" in result

def test_ec2_stakeholder_missing_text():
    """Test EC2 stakeholder with missing text"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_ec2_stakeholder(request)
        assert "Usage: <instance-id|instance-name> [claim|remove|check]" in result

def test_ec2_stakeholder_claim_failed_operation():
    """Test EC2 stakeholder claim when the operation fails"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (False, "failed")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "Failed to claim `test-instance`" in result

def test_ec2_stakeholder_claim_unknown_result():
    """Test EC2 stakeholder claim with unknown result from add_stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (True, "unknown_result")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "Failed to claim `test-instance`" in result

def test_ec2_stakeholder_remove_unknown_result():
    """Test EC2 stakeholder remove with unknown result from remove_stakeholder"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.remove_stakeholder') as mock_remove_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_remove_stakeholder.return_value = (True, "unknown_result")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d remove'}
            
            result = handle_ec2_stakeholder(request)
            assert "Failed to remove stakeholder status for `test-instance`" in result

def test_ec2_stakeholder_remove_and_delete_tag():
    """Test EC2 stakeholder remove when it's the last stakeholder and tag gets deleted"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.remove_stakeholder') as mock_remove_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_remove_stakeholder.return_value = (True, "removed_and_deleted_tag")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'i-0df9c53001c5c837d remove'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are no longer a stakeholder for `test-instance`" in result

def test_ec2_stakeholder_with_instance_name():
    """Test EC2 stakeholder using instance name instead of ID"""
    with app.app_context():
        with patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.can_control_instance_by_id') as mock_can_control, \
             patch('src.handlers.get_instance_name') as mock_get_name, \
             patch('src.handlers.add_stakeholder') as mock_add_stakeholder:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_can_control.return_value = True
            mock_get_name.return_value = 'test-instance'
            mock_add_stakeholder.return_value = (True, "added")
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn', 'text': 'test-instance claim'}
            
            result = handle_ec2_stakeholder(request)
            assert "You are now a stakeholder for `test-instance`" in result 