import logging
from datetime import datetime, time, timezone
from dateutil import parser
import json
import os
from src.aws_client import get_power_schedule_tags, set_power_schedule_tags, delete_power_schedule_tags, can_control_instance_by_id

logger = logging.getLogger(__name__)

def _log_schedule_operation(operation, instance_id, details=None, success=True, error=None):
    """Log schedule operations for auditing purposes"""
    timestamp = datetime.now(timezone.utc).isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_entry = {
        'timestamp': timestamp,
        'schedule_operation': operation,
        'instance_id': instance_id,
        'details': details,
        'status': status,
        'pod_name': os.environ.get('HOSTNAME', 'unknown'),
        'namespace': os.environ.get('POD_NAMESPACE', 'unknown')
    }
    if error:
        log_entry['error'] = str(error)
    
    logger.info(f"SCHEDULE_AUDIT: {json.dumps(log_entry)}")

def parse_time(time_str):
    """Parse time string to time object, supporting various formats"""
    try:
        # Handle None or empty input
        if not time_str or not time_str.strip():
            logger.error(f"Empty or None time string provided")
            _log_schedule_operation("parse_time", "time", {"time_str": time_str, "error": "empty_input"}, False)
            return None
        
        # Normalize the input
        time_str = time_str.strip().lower()
        
        # Handle common variations
        if time_str.endswith('am') or time_str.endswith('pm'):
            # Ensure there's a space before am/pm if there's no colon
            if ':' not in time_str and len(time_str) <= 4:
                # Format like "5am" -> "5:00am"
                time_str = time_str[:-2] + ':00' + time_str[-2:]
        
        # Parse using dateutil
        parsed = parser.parse(time_str)
        
        # Validate the parsed time is reasonable
        time_obj = parsed.time()
        if time_obj.hour > 23 or time_obj.minute > 59:
            logger.error(f"Invalid time values: hour={time_obj.hour}, minute={time_obj.minute}")
            _log_schedule_operation("parse_time", "time", {
                "time_str": time_str, 
                "error": "invalid_time_values",
                "hour": time_obj.hour,
                "minute": time_obj.minute
            }, False)
            return None
        
        logger.info(f"Successfully parsed time '{time_str}' to {time_obj}")
        return time_obj
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        _log_schedule_operation("parse_time", "time", {"time_str": time_str, "error": str(e)}, False)
        return None

def format_time_for_tag(time_obj):
    """Format time object to string format suitable for EC2 tags"""
    if time_obj is None:
        return None
    return time_obj.strftime('%H:%M')

def get_schedule(instance_id):
    """Get schedule for an instance from EC2 tags"""
    try:
        logger.info(f"Getting schedule for instance {instance_id} from EC2 tags")
        schedule_tags = get_power_schedule_tags(instance_id)
        
        if not schedule_tags:
            _log_schedule_operation("get_schedule", instance_id, {
                "schedule_found": False,
                "note": "no_schedule_tags_found"
            })
            return None
        
        # Parse the time strings back to time objects for consistency
        schedule = {}
        if 'on_time' in schedule_tags:
            on_time = parse_time(schedule_tags['on_time'])
            if on_time:
                schedule['start_time'] = format_time_for_tag(on_time)
        
        if 'off_time' in schedule_tags:
            off_time = parse_time(schedule_tags['off_time'])
            if off_time:
                schedule['stop_time'] = format_time_for_tag(off_time)
        
        _log_schedule_operation("get_schedule", instance_id, {
            "schedule_found": True,
            "schedule": schedule,
            "raw_tags": schedule_tags
        })
        return schedule
        
    except Exception as e:
        logger.error(f"Error getting schedule for {instance_id}: {e}")
        _log_schedule_operation("get_schedule", instance_id, {
            "error": str(e)
        }, False, e)
        return None

def set_schedule(instance_id, start_time, stop_time):
    """Set schedule for an instance using EC2 tags"""
    try:
        logger.info(f"Setting schedule for instance {instance_id}: {start_time} to {stop_time}")
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            logger.error(f"Cannot set schedule for instance {instance_id}: not authorized to control this instance")
            _log_schedule_operation("set_schedule", instance_id, {
                "error": "instance_not_controllable",
                "start_time": str(start_time),
                "stop_time": str(stop_time)
            }, False)
            return False
        
        # Format times for EC2 tags
        on_time_str = format_time_for_tag(start_time)
        off_time_str = format_time_for_tag(stop_time)
        
        if not on_time_str or not off_time_str:
            logger.error(f"Invalid time format for instance {instance_id}")
            _log_schedule_operation("set_schedule", instance_id, {
                "error": "invalid_time_format",
                "start_time": str(start_time),
                "stop_time": str(stop_time)
            }, False)
            return False
        
        # Set the EC2 tags
        success = set_power_schedule_tags(instance_id, on_time_str, off_time_str)
        
        if success:
            _log_schedule_operation("set_schedule", instance_id, {
                "start_time": on_time_str,
                "stop_time": off_time_str,
                "aws_operation_success": True
            })
        else:
            _log_schedule_operation("set_schedule", instance_id, {
                "error": "aws_operation_failed",
                "start_time": on_time_str,
                "stop_time": off_time_str
            }, False)
        
        return success
        
    except Exception as e:
        logger.error(f"Error setting schedule for {instance_id}: {e}")
        _log_schedule_operation("set_schedule", instance_id, {
            "error": str(e),
            "start_time": str(start_time),
            "stop_time": str(stop_time)
        }, False, e)
        return False

def delete_schedule(instance_id):
    """Delete schedule for an instance by removing EC2 tags"""
    try:
        logger.info(f"Deleting schedule for instance {instance_id}")
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            logger.error(f"Cannot delete schedule for instance {instance_id}: not authorized to control this instance")
            _log_schedule_operation("delete_schedule", instance_id, {
                "error": "instance_not_controllable"
            }, False)
            return False
        
        # Delete the EC2 tags
        success = delete_power_schedule_tags(instance_id)
        
        if success:
            _log_schedule_operation("delete_schedule", instance_id, {
                "aws_operation_success": True
            })
        else:
            _log_schedule_operation("delete_schedule", instance_id, {
                "error": "aws_operation_failed"
            }, False)
        
        return success
        
    except Exception as e:
        logger.error(f"Error deleting schedule for {instance_id}: {e}")
        _log_schedule_operation("delete_schedule", instance_id, {
            "error": str(e)
        }, False, e)
        return False

def format_schedule_display(schedule):
    """Format schedule for display"""
    if not schedule:
        return "No schedule set"
    
    start_time = schedule.get('start_time', '')
    stop_time = schedule.get('stop_time', '')
    
    # Convert 24-hour format to 12-hour format for display
    try:
        start_dt = datetime.strptime(start_time, '%H:%M')
        stop_dt = datetime.strptime(stop_time, '%H:%M')
        
        start_display = start_dt.strftime('%I:%M %p').lstrip('0')
        stop_display = stop_dt.strftime('%I:%M %p').lstrip('0')
        
        return f"{start_display} to {stop_display}"
    except ValueError:
        return f"{start_time} to {stop_time}" 