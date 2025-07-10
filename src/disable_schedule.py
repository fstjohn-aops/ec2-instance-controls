import logging
from datetime import datetime, timezone, timedelta
from dateutil import parser
import json
import os
from src.aws_client import get_disable_schedule_tag, set_disable_schedule_tag, delete_disable_schedule_tag, can_control_instance_by_id

logger = logging.getLogger(__name__)

def _log_disable_schedule_operation(operation, instance_id, details=None, success=True, error=None):
    """Log disable schedule operations for auditing purposes"""
    timestamp = datetime.now(timezone.utc).isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_entry = {
        'timestamp': timestamp,
        'disable_schedule_operation': operation,
        'instance_id': instance_id,
        'details': details,
        'status': status,
        'pod_name': os.environ.get('HOSTNAME', 'unknown'),
        'namespace': os.environ.get('POD_NAMESPACE', 'unknown')
    }
    if error:
        log_entry['error'] = str(error)
    
    logger.info(f"DISABLE_SCHEDULE_AUDIT: {json.dumps(log_entry)}")

def parse_hours(hours_str):
    """Parse hours string in 'Nh' format (e.g., '2h', '24h')"""
    try:
        # Handle None or empty input
        if not hours_str or not hours_str.strip():
            logger.error(f"Empty or None hours string provided")
            _log_disable_schedule_operation("parse_hours", "hours", {"hours_str": hours_str, "error": "empty_input"}, False)
            return None
        
        # Normalize the input
        hours_str = hours_str.strip().lower()
        
        # Check if it ends with 'h'
        if not hours_str.endswith('h'):
            logger.error(f"Hours string must end with 'h': {hours_str}")
            _log_disable_schedule_operation("parse_hours", "hours", {"hours_str": hours_str, "error": "must_end_with_h"}, False)
            return None
        
        # Extract the number part
        try:
            hours = int(hours_str[:-1])
        except ValueError:
            logger.error(f"Invalid number in hours string: {hours_str}")
            _log_disable_schedule_operation("parse_hours", "hours", {"hours_str": hours_str, "error": "invalid_number"}, False)
            return None
        
        # Validate minimum 1 hour
        if hours < 1:
            logger.error(f"Hours must be at least 1: {hours}")
            _log_disable_schedule_operation("parse_hours", "hours", {"hours_str": hours_str, "hours": hours, "error": "below_minimum"}, False)
            return None
        
        logger.info(f"Successfully parsed hours '{hours_str}' to {hours}")
        return hours
    except Exception as e:
        logger.error(f"Error parsing hours '{hours_str}': {e}")
        _log_disable_schedule_operation("parse_hours", "hours", {"hours_str": hours_str, "error": str(e)}, False)
        return None



def get_disable_schedule(instance_id):
    """Get disable schedule for an instance from EC2 tags"""
    try:
        logger.info(f"Getting disable schedule for instance {instance_id} from EC2 tags")
        disable_until = get_disable_schedule_tag(instance_id)
        
        if not disable_until:
            _log_disable_schedule_operation("get_disable_schedule", instance_id, {
                "disable_schedule_found": False,
                "note": "no_disable_schedule_tag_found"
            })
            return None
        
        # Parse the datetime string back to datetime object
        try:
            disable_datetime = datetime.fromisoformat(disable_until)
            if disable_datetime.tzinfo is None:
                # Assume UTC if no timezone specified
                disable_datetime = disable_datetime.replace(tzinfo=timezone.utc)
        except ValueError:
            _log_disable_schedule_operation("get_disable_schedule", instance_id, {
                "error": "invalid_datetime_format",
                "raw_tag_value": disable_until
            }, False)
            return None
        
        _log_disable_schedule_operation("get_disable_schedule", instance_id, {
            "disable_schedule_found": True,
            "disable_until": disable_until,
            "parsed_datetime": disable_datetime.isoformat()
        })
        return disable_datetime
        
    except Exception as e:
        logger.error(f"Error getting disable schedule for {instance_id}: {e}")
        _log_disable_schedule_operation("get_disable_schedule", instance_id, {
            "error": str(e)
        }, False, e)
        return None

def set_disable_schedule(instance_id, hours):
    """Set disable schedule for an instance using EC2 tags"""
    try:
        logger.info(f"Setting disable schedule for instance {instance_id} for {hours} hours")
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            logger.error(f"Cannot set disable schedule for instance {instance_id}: not authorized to control this instance")
            _log_disable_schedule_operation("set_disable_schedule", instance_id, {
                "error": "instance_not_controllable",
                "hours": hours
            }, False)
            return False
        
        # Calculate disable until datetime (current time + hours)
        now = datetime.now(timezone.utc)
        disable_until = now + timedelta(hours=hours)
        
        # Format datetime for EC2 tags (ISO format)
        disable_until_str = disable_until.isoformat()
        
        # Set the EC2 tag
        success = set_disable_schedule_tag(instance_id, disable_until_str)
        
        if success:
            _log_disable_schedule_operation("set_disable_schedule", instance_id, {
                "hours": hours,
                "disable_until": disable_until_str,
                "aws_operation_success": True
            })
        else:
            _log_disable_schedule_operation("set_disable_schedule", instance_id, {
                "error": "aws_operation_failed",
                "hours": hours,
                "disable_until": disable_until_str
            }, False)
        
        return success
        
    except Exception as e:
        logger.error(f"Error setting disable schedule for {instance_id}: {e}")
        _log_disable_schedule_operation("set_disable_schedule", instance_id, {
            "error": str(e),
            "hours": hours
        }, False, e)
        return False

def delete_disable_schedule(instance_id):
    """Delete disable schedule for an instance by removing EC2 tags"""
    try:
        logger.info(f"Deleting disable schedule for instance {instance_id}")
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            logger.error(f"Cannot delete disable schedule for instance {instance_id}: not authorized to control this instance")
            _log_disable_schedule_operation("delete_disable_schedule", instance_id, {
                "error": "instance_not_controllable"
            }, False)
            return False
        
        # Delete the EC2 tag
        success = delete_disable_schedule_tag(instance_id)
        
        if success:
            _log_disable_schedule_operation("delete_disable_schedule", instance_id, {
                "aws_operation_success": True
            })
        else:
            _log_disable_schedule_operation("delete_disable_schedule", instance_id, {
                "error": "aws_operation_failed"
            }, False)
        
        return success
        
    except Exception as e:
        logger.error(f"Error deleting disable schedule for {instance_id}: {e}")
        _log_disable_schedule_operation("delete_disable_schedule", instance_id, {
            "error": str(e)
        }, False, e)
        return False

def format_disable_schedule_display(disable_datetime):
    """Format disable schedule for display"""
    if not disable_datetime:
        return "No disable schedule set"
    
    # Calculate remaining time
    now = datetime.now(timezone.utc)
    if now >= disable_datetime:
        return "No disable schedule set (expired)"
    
    remaining = disable_datetime - now
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)
    
    if hours > 0:
        if minutes > 0:
            return f"Disabled for {hours}h {minutes}m"
        else:
            return f"Disabled for {hours}h"
    else:
        return f"Disabled for {minutes}m"

def is_schedule_disabled(instance_id):
    """Check if schedule is currently disabled for an instance"""
    try:
        disable_until = get_disable_schedule(instance_id)
        if not disable_until:
            return False
        
        # Check if the disable period has expired
        now = datetime.now(timezone.utc)
        is_disabled = now < disable_until
        
        logger.info(f"Schedule disable check for {instance_id}: disabled until {disable_until}, currently disabled: {is_disabled}")
        return is_disabled
        
    except Exception as e:
        logger.error(f"Error checking if schedule is disabled for {instance_id}: {e}")
        return False 