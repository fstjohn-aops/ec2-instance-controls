import logging
from datetime import datetime, time
from dateutil import parser
import json
import os

logger = logging.getLogger(__name__)

# Simple file-based storage for schedules
SCHEDULE_FILE = 'schedules.json'

def _log_schedule_operation(operation, instance_id, details=None, success=True):
    """Log schedule operations for auditing purposes"""
    timestamp = datetime.utcnow().isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_entry = {
        'timestamp': timestamp,
        'schedule_operation': operation,
        'instance_id': instance_id,
        'details': details,
        'status': status
    }
    logger.info(f"SCHEDULE_AUDIT: {json.dumps(log_entry)}")

def _load_schedules():
    """Load schedules from file"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                schedules = json.load(f)
                logger.info(f"Loaded {len(schedules)} schedules from {SCHEDULE_FILE}")
                return schedules
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading schedules: {e}")
            _log_schedule_operation("load_schedules", "file", {"error": str(e)}, False)
            return {}
    return {}

def _save_schedules(schedules):
    """Save schedules to file"""
    try:
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        logger.info(f"Saved {len(schedules)} schedules to {SCHEDULE_FILE}")
        _log_schedule_operation("save_schedules", "file", {"schedule_count": len(schedules)})
        return True
    except IOError as e:
        logger.error(f"Error saving schedules: {e}")
        _log_schedule_operation("save_schedules", "file", {"error": str(e)}, False)
        return False

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
    """Get schedule for an instance"""
    schedules = _load_schedules()
    schedule = schedules.get(instance_id)
    
    _log_schedule_operation("get_schedule", instance_id, {
        "schedule_found": schedule is not None,
        "schedule": schedule
    })
    
    return schedule

def set_schedule(instance_id, start_time, stop_time):
    """Set schedule for an instance"""
    schedules = _load_schedules()
    
    # Convert time objects to string format for JSON serialization
    schedule = {
        'start_time': start_time.strftime('%H:%M'),
        'stop_time': stop_time.strftime('%H:%M')
    }
    
    # Check if schedule already exists
    existing_schedule = schedules.get(instance_id)
    
    schedules[instance_id] = schedule
    
    if _save_schedules(schedules):
        logger.info(f"Schedule set for {instance_id}: {start_time.strftime('%H:%M')} to {stop_time.strftime('%H:%M')}")
        _log_schedule_operation("set_schedule", instance_id, {
            "start_time": start_time.strftime('%H:%M'),
            "stop_time": stop_time.strftime('%H:%M'),
            "previous_schedule": existing_schedule
        })
        return True
    else:
        logger.error(f"Failed to save schedule for {instance_id}")
        _log_schedule_operation("set_schedule", instance_id, {
            "start_time": start_time.strftime('%H:%M'),
            "stop_time": stop_time.strftime('%H:%M'),
            "error": "save_failed"
        }, False)
        return False

def delete_schedule(instance_id):
    """Delete schedule for an instance"""
    schedules = _load_schedules()
    
    if instance_id in schedules:
        deleted_schedule = schedules[instance_id]
        del schedules[instance_id]
        
        if _save_schedules(schedules):
            logger.info(f"Schedule deleted for {instance_id}")
            _log_schedule_operation("delete_schedule", instance_id, {
                "deleted_schedule": deleted_schedule
            })
            return True
        else:
            logger.error(f"Failed to delete schedule for {instance_id}")
            _log_schedule_operation("delete_schedule", instance_id, {
                "error": "save_failed"
            }, False)
            return False
    else:
        logger.info(f"No schedule found to delete for {instance_id}")
        _log_schedule_operation("delete_schedule", instance_id, {
            "error": "schedule_not_found"
        }, False)
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