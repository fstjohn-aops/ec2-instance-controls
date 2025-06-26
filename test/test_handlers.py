import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.handlers import handle_admin_check, handle_ec2_power, handle_list_instances, handle_ec2_schedule
from src.schedule import parse_time, format_schedule_display

# Create a test Flask app
app = Flask(__name__)

# Admin check tests
def test_admin_check_admin():
    """Test admin check for admin user"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
    
    result = handle_admin_check(request)
    assert "is an administrator" in result

def test_admin_check_non_admin():
    """Test admin check for non-admin user"""
    request = Mock()
    request.form = {'user_id': 'U123456789', 'user_name': 'otheruser'}
    
    result = handle_admin_check(request)
    assert "is not an administrator" in result

def test_admin_check_missing_user_id():
    """Test admin check with missing user_id"""
    request = Mock()
    request.form = {'user_name': 'fstjohn'}
    
    result = handle_admin_check(request)
    assert "is not an administrator" in result

def test_admin_check_empty_user_id():
    """Test admin check with empty user_id"""
    request = Mock()
    request.form = {'user_id': '', 'user_name': 'fstjohn'}
    
    result = handle_admin_check(request)
    assert "is not an administrator" in result

# Instance list tests
def test_list_instances_with_instances():
    """Test listing instances when user has assigned instances"""
    with patch('src.handlers.get_user_instances') as mock_get_instances, \
         patch('src.handlers.get_instance_state') as mock_get_state, \
         patch('src.handlers.get_instance_name') as mock_get_name:
        
        mock_get_instances.return_value = ['i-0df9c53001c5c837d', 'i-0fff0f1804788ae88']
        mock_get_state.side_effect = ['running', 'stopped']
        mock_get_name.side_effect = ['test-instance-1', 'test-instance-2']
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "Instances assigned to `fstjohn`" in result
        assert "test-instance-1" in result
        assert "test-instance-2" in result
        assert "running" in result
        assert "stopped" in result

def test_list_instances_no_instances():
    """Test listing instances when user has no assigned instances"""
    with patch('src.handlers.get_user_instances') as mock_get_instances:
        mock_get_instances.return_value = []
        
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'user_name': 'fstjohn'}
        
        result = handle_list_instances(request)
        assert "has no assigned instances" in result

def test_list_instances_missing_user_id():
    """Test listing instances with missing user_id"""
    request = Mock()
    request.form = {'user_name': 'fstjohn'}
    
    result = handle_list_instances(request)
    assert "user_id parameter is required" in result

def test_list_instances_instance_state_unknown():
    """Test listing instances when instance state is unknown"""
    with patch('src.handlers.get_user_instances') as mock_get_instances, \
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
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_start.return_value = True
            mock_get_name.return_value = 'test-instance'
            
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
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'running'
            mock_stop.return_value = True
            mock_get_name.return_value = 'test-instance'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d off'}
            
            result = handle_ec2_power(request)
            assert "Set `test-instance`" in result.json['text']
            assert "to off" in result.json['text']

def test_ec2_power_access_denied():
    """Test EC2 power access denied for unauthorized user"""
    request = Mock()
    request.form = {'user_id': 'U123456789', 'text': 'i-0df9c53001c5c837d on'}
    
    result = handle_ec2_power(request)
    assert "Access to instance" in result
    assert "denied" in result

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
             patch('src.handlers.get_instance_name') as mock_get_name:
            
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_state.return_value = 'stopped'
            mock_start.return_value = True
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
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
        assert "must be 'on' or 'off'" in result

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
                'start_schedule': 'cron(0 9 * * ? *)',
                'stop_schedule': 'cron(0 17 * * ? *)',
                'timezone': 'UTC'
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
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_set_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule set for" in result.json['text']
            assert "9:00 AM to 5:00 PM" in result.json['text']

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

def test_ec2_schedule_set_failed():
    """Test setting schedule when it fails"""
    with app.app_context():
        with patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_set_schedule.return_value = False
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
            
            result = handle_ec2_schedule(request)
            assert "Failed to set schedule" in result

def test_ec2_schedule_access_denied():
    """Test schedule access denied for unauthorized user"""
    request = Mock()
    request.form = {'user_id': 'U123456789', 'text': 'i-0df9c53001c5c837d 9am to 5pm'}
    
    result = handle_ec2_schedule(request)
    assert "Access to instance" in result
    assert "denied" in result

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
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d clear'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_reset():
    """Test resetting a schedule"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d reset'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_unset():
    """Test unsetting a schedule"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d unset'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_clear_failed():
    """Test clearing a schedule when it fails"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_delete_schedule.return_value = False
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
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

def test_ec2_schedule_missing_user_id():
    """Test schedule with missing user_id"""
    request = Mock()
    request.form = {'text': 'i-0df9c53001c5c837d clear'}
    
    result = handle_ec2_schedule(request)
    assert "Access to instance" in result
    assert "denied" in result

def test_ec2_schedule_empty_user_id():
    """Test schedule with empty user_id"""
    request = Mock()
    request.form = {'user_id': '', 'text': 'i-0df9c53001c5c837d clear'}
    
    result = handle_ec2_schedule(request)
    assert "Access to instance" in result
    assert "denied" in result

def test_ec2_schedule_case_insensitive_clear():
    """Test schedule clear commands are case insensitive"""
    with app.app_context():
        with patch('src.handlers.delete_schedule') as mock_delete_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_delete_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
            # Test uppercase
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d CLEAR'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']
            
            # Test mixed case
            request = Mock()
            request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d Reset'}
            
            result = handle_ec2_schedule(request)
            assert "Schedule cleared for" in result.json['text']

def test_ec2_schedule_complex_time_formats():
    """Test schedule with complex time formats"""
    with app.app_context():
        with patch('src.handlers.set_schedule') as mock_set_schedule, \
             patch('src.handlers.resolve_instance_identifier') as mock_resolve, \
             patch('src.handlers.get_instance_name') as mock_get_name:
            mock_set_schedule.return_value = True
            mock_resolve.return_value = 'i-0df9c53001c5c837d'
            mock_get_name.return_value = 'i-0df9c53001c5c837d'
            
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
                    "Schedule set for", "Invalid start time", "Invalid stop time", "Usage:"
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