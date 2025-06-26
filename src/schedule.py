import logging
from datetime import datetime, time, timezone
from dateutil import parser
import json
import os

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
        logger.info(f"Successfully parsed time '{time_str}' to {parsed.time()}")
        return parsed.time()
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        _log_schedule_operation("parse_time", "time", {"time_str": time_str, "error": str(e)}, False)
        return None

def get_schedule(instance_id):
    """Get schedule for an instance - no-op until EC2 tag implementation"""
    logger.info(f"Schedule functionality temporarily disabled - will be implemented with EC2 tags for {instance_id}")
    _log_schedule_operation("get_schedule", instance_id, {
        "schedule_found": False,
        "note": "schedule_functionality_disabled_ec2_tags_coming"
    })
    return None

def set_schedule(instance_id, start_time, stop_time):
    """Set schedule for an instance - no-op until EC2 tag implementation"""
    logger.info(f"Schedule functionality temporarily disabled - will be implemented with EC2 tags for {instance_id}")
    _log_schedule_operation("set_schedule", instance_id, {
        "start_time": start_time.strftime('%H:%M'),
        "stop_time": stop_time.strftime('%H:%M'),
        "note": "schedule_functionality_disabled_ec2_tags_coming"
    })
    return False

def delete_schedule(instance_id):
    """Delete schedule for an instance - no-op until EC2 tag implementation"""
    logger.info(f"Schedule functionality temporarily disabled - will be implemented with EC2 tags for {instance_id}")
    _log_schedule_operation("delete_schedule", instance_id, {
        "note": "schedule_functionality_disabled_ec2_tags_coming"
    })
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