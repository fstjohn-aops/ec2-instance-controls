import pytest
from unittest.mock import Mock, patch
from flask import Flask
from src.handlers import handle_admin_check, handle_ec2_power

# Create a test Flask app
app = Flask(__name__)

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

def test_ec2_power_valid():
    """Test EC2 power with valid input"""
    with app.app_context():
        request = Mock()
        request.form = {'user_id': 'U08QYU6AX0V', 'text': 'i-0df9c53001c5c837d on'}
        
        result = handle_ec2_power(request)
        assert "Set `i-0df9c53001c5c837d` to on" in result.json['text']

def test_ec2_power_invalid_format():
    """Test EC2 power with invalid format"""
    request = Mock()
    request.form = {'user_id': 'U08QYU6AX0V', 'text': 'invalid'}
    
    result = handle_ec2_power(request)
    assert "Instance `invalid` not found" in result

def test_ec2_power_invalid_state():
    """Test EC2 power with invalid power state"""
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