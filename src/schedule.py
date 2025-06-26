import logging
from datetime import datetime, time
from dateutil import parser
import json
import os

logger = logging.getLogger(__name__)

# Simple file-based storage for schedules
SCHEDULE_FILE = 'schedules.json'

def _load_schedules():
    """Load schedules from file"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading schedules: {e}")
            return {}
    return {}

def _save_schedules(schedules):
    """Save schedules to file"""
    try:
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        return True
    except IOError as e:
        logger.error(f"Error saving schedules: {e}")
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
        return parsed.time()
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        return None

def get_schedule(instance_id):
    """Get schedule for an instance"""
    schedules = _load_schedules()
    return schedules.get(instance_id)

def set_schedule(instance_id, start_time, stop_time):
    """Set schedule for an instance"""
    schedules = _load_schedules()
    
    # Convert time objects to string format for JSON serialization
    schedule = {
        'start_time': start_time.strftime('%H:%M'),
        'stop_time': stop_time.strftime('%H:%M')
    }
    
    schedules[instance_id] = schedule
    
    if _save_schedules(schedules):
        logger.info(f"Schedule set for {instance_id}: {start_time.strftime('%H:%M')} to {stop_time.strftime('%H:%M')}")
        return True
    else:
        logger.error(f"Failed to save schedule for {instance_id}")
        return False

def delete_schedule(instance_id):
    """Delete schedule for an instance"""
    schedules = _load_schedules()
    
    if instance_id in schedules:
        del schedules[instance_id]
        if _save_schedules(schedules):
            logger.info(f"Schedule deleted for {instance_id}")
            return True
        else:
            logger.error(f"Failed to delete schedule for {instance_id}")
            return False
    
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