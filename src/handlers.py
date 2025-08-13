import logging
import re
import json
from datetime import datetime, timezone
from flask import jsonify
from src.aws_client import get_instance_state, start_instance, stop_instance, restart_instance, resolve_instance_identifier, get_instance_name, fuzzy_search_instances, can_control_instance_by_id, add_stakeholder, remove_stakeholder, is_user_stakeholder
from src.auth import get_all_region_instances
from src.schedule import parse_time, get_schedule, set_schedule, format_schedule_display, delete_schedule
from src.disable_schedule import parse_hours, get_disable_schedule, set_disable_schedule, delete_disable_schedule, format_disable_schedule_display
import os

logger = logging.getLogger(__name__)

# Centralized command alias maps
ACTION_ALIASES_POWER = {
	'on': {'on', 'start', 'up', 'boot', 'poweron', 'enable'},
	'off': {'off', 'stop', 'down', 'halt', 'shutdown', 'poweroff',},
	'restart': {'restart', 'reboot', 'bounce', 'cycle', 'reload'}
}

ACTION_ALIASES_STAKEHOLDER = {
	'claim': {'claim', 'add', 'join', 'register', 'own'},
	'remove': {'remove', 'unclaim', 'leave', 'unregister', 'drop', 'rm', 'delete'},
	'check': {'check', 'status', 'show', 'view', 'see', 'info', 'get', 'stat'}
}

ALIASES_SCHEDULE_CLEAR = {'clear', 'reset', 'unset', 'no', 'remove', 'delete', 'none', 'empty'}
ALIASES_DISABLE_CANCEL = {'cancel', 'clear', 'reset', 'unset', 'no', 'remove', 'delete', 'resume', 'enable', 're-enable', 'reenable', 'unpause', 'continue'}


def normalize_command(value, alias_map):
	"""Normalize a user-provided command to its canonical value using alias_map.
	Returns the input lowercased if no alias matches (so existing validation can handle it)."""
	v = value.lower()
	for canonical, aliases in alias_map.items():
		if v == canonical or v in aliases:
			return canonical
	return v

def _log_user_action(user_id, user_name, action, target, details=None, success=True):
    """Log user actions for auditing purposes"""
    timestamp = datetime.now(timezone.utc).isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_entry = {
        'timestamp': timestamp,
        'user_id': user_id,
        'user_name': user_name,
        'action': action,
        'target': target,
        'details': details,
        'status': status,
        'pod_name': os.environ.get('HOSTNAME', 'unknown'),
        'namespace': os.environ.get('POD_NAMESPACE', 'unknown'),
        'deployment': os.environ.get('DEPLOYMENT_NAME', 'unknown')
    }
    logger.info(f"AUDIT: {json.dumps(log_entry)}")

def _is_valid_instance_id(instance_id):
    """Validate EC2 instance ID format"""
    # EC2 instance IDs follow pattern: i- followed by 8 or 17 hex characters
    pattern = r'^i-[0-9a-f]{8}$|^i-[0-9a-f]{17}$'
    return bool(re.match(pattern, instance_id))

def handle_ec2_power(request):
    """Handle the EC2 power control endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    text = request.form.get('text', '').strip()
    
    # Parse text: "instance-id" or "instance-name" or "instance-id on" or "instance-name on"
    parts = text.split()
    
    if len(parts) == 1:
        # Just instance identifier - return current state
        instance_identifier = parts[0]
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_power_status", instance_identifier, {"error": "instance_not_found"}, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Get current state using the resolved instance ID
        logger.info(f"Calling get_instance_state with resolved instance_id: {instance_id}")
        current_state = get_instance_state(instance_id)
        if current_state:
            # Get instance name for display if available
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            
            _log_user_action(user_id, user_name, "ec2_power_status", instance_id, {
                "instance_name": instance_name,
                "current_state": current_state,
                "original_identifier": instance_identifier
            })
            
            return f"Instance `{display_name}` ({instance_id}) is currently {current_state}"
        else:
            _log_user_action(user_id, user_name, "ec2_power_status", instance_id, {
                "error": "instance_not_found_in_aws",
                "original_identifier": instance_identifier
            }, False)
            return f"Instance `{instance_identifier}` not found"
    
    elif len(parts) == 2:
        # Instance identifier and power state - change state
        instance_identifier, power_state = parts
        
        # Normalize power state using aliases
        power_state = normalize_command(power_state, ACTION_ALIASES_POWER)
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_power_change", instance_identifier, {
                "power_state": power_state,
                "error": "instance_not_found"
            }, False)
            return f"Instance `{instance_identifier}` not found"
        
        if power_state not in ['on', 'off', 'restart']:
            _log_user_action(user_id, user_name, "ec2_power_change", instance_id, {
                "power_state": power_state,
                "error": "invalid_power_state"
            }, False)
            return "Power state must be 'on', 'off', or 'restart'."
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            _log_user_action(user_id, user_name, "ec2_power_change", instance_id, {
                "power_state": power_state,
                "error": "instance_not_controllable",
                "instance_name": instance_name
            }, False)
            return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
        
        # Get instance name for display if available
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        
        # Log the power change attempt
        _log_user_action(user_id, user_name, "ec2_power_change", instance_id, {
            "instance_name": instance_name,
            "power_state": power_state,
            "original_identifier": instance_identifier
        })
        
        # Respond immediately
        response = jsonify({
            'response_type': 'ephemeral',
            'text': f"Set `{display_name}` ({instance_id}) to {power_state}"
        })
        
        # Then do the AWS operation using the resolved instance ID
        logger.info(f"Calling get_instance_state with resolved instance_id: {instance_id}")
        current_state = get_instance_state(instance_id)
        if current_state:
            logger.info(f"AWS: Instance `{instance_id}` current state is {current_state}")
            
            # Change the state
            if power_state == 'on':
                success = start_instance(instance_id)
                # Check for specific error cases and provide user-friendly messages
                if not success:
                    if current_state == 'running':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"`{display_name}` ({instance_id}) is already running"
                        })
                    elif current_state == 'pending':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"`{display_name}` ({instance_id}) is already starting"
                        })
                    elif current_state == 'stopping':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot start `{display_name}` ({instance_id}) - instance is currently stopping"
                        })
                    elif current_state == 'stopped':
                        # This should succeed, but if it doesn't, it's likely an AWS error
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Failed to start `{display_name}` ({instance_id}) - please try again"
                        })
                    else:
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot start `{display_name}` ({instance_id}) - instance is in an invalid state ({current_state})"
                        })
            elif power_state == 'off':
                success = stop_instance(instance_id)
                # Check for specific error cases and provide user-friendly messages
                if not success:
                    if current_state == 'stopped':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"`{display_name}` ({instance_id}) is already stopped"
                        })
                    elif current_state == 'stopping':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"`{display_name}` ({instance_id}) is already stopping"
                        })
                    elif current_state == 'pending':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot stop `{display_name}` ({instance_id}) - instance is currently starting"
                        })
                    elif current_state == 'running':
                        # This should succeed, but if it doesn't, it's likely an AWS error
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Failed to stop `{display_name}` ({instance_id}) - please try again"
                        })
                    else:
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot stop `{display_name}` ({instance_id}) - instance is in an invalid state ({current_state})"
                        })
            elif power_state == 'restart':
                success = restart_instance(instance_id)
                # Check for specific error cases and provide user-friendly messages
                if not success:
                    if current_state == 'stopped':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot restart `{display_name}` ({instance_id}) - instance is currently stopped"
                        })
                    elif current_state == 'pending':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot restart `{display_name}` ({instance_id}) - instance is currently starting"
                        })
                    elif current_state == 'stopping':
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot restart `{display_name}` ({instance_id}) - instance is currently stopping"
                        })
                    elif current_state == 'running':
                        # This should succeed, but if it doesn't, it's likely an AWS error
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Failed to restart `{display_name}` ({instance_id}) - please try again"
                        })
                    else:
                        response = jsonify({
                            'response_type': 'ephemeral',
                            'text': f"Cannot restart `{display_name}` ({instance_id}) - instance is in an invalid state ({current_state})"
                        })
            
            # Log the AWS operation result
            _log_user_action(user_id, user_name, f"ec2_power_{power_state}", instance_id, {
                "instance_name": instance_name,
                "previous_state": current_state,
                "aws_operation_success": success
            }, success)
        else:
            logger.error(f"AWS: Instance `{instance_id}` not found")
            _log_user_action(user_id, user_name, f"ec2_power_{power_state}", instance_id, {
                "error": "instance_not_found_in_aws"
            }, False)
            # Update response for the case where instance state couldn't be determined
            response = jsonify({
                'response_type': 'ephemeral',
                'text': f"Failed to determine state of `{display_name}` ({instance_id}) - please try again"
            })
        
        return response
    
    else:
        _log_user_action(user_id, user_name, "ec2_power", "invalid", {"error": "invalid_format", "text": text}, False)
        return "Usage: <instance-id|instance-name> [on|off|restart]"

def handle_list_instances(request):
    """Handle the list instances endpoint - returns all instances in the AWS region that can be controlled by this service"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    
    instances = get_all_region_instances()
    
    if not instances:
        _log_user_action(user_id, user_name, "list_instances", "all", {"instance_count": 0})
        return f"No controllable instances found in the AWS region. Add the `EC2ControlsEnabled` tag with a truthy value to instances you want to control."
    
    # Get current state for each instance
    instance_states = []
    instance_details = []
    for instance_id in instances:
        state = get_instance_state(instance_id)
        instance_name = get_instance_name(instance_id)
        
        instance_detail = {
            "instance_id": instance_id,
            "instance_name": instance_name,
            "state": state
        }
        instance_details.append(instance_detail)
        
        if state:
            if instance_name:
                instance_states.append(f"`{instance_name}` ({instance_id}) - {state}")
            else:
                instance_states.append(f"`{instance_id}` - {state}")
        else:
            if instance_name:
                instance_states.append(f"`{instance_name}` ({instance_id}) - unknown state")
            else:
                instance_states.append(f"`{instance_id}` - unknown state")
    
    # Log the list instances action
    _log_user_action(user_id, user_name, "list_instances", "all", {
        "instance_count": len(instances),
        "instances": instance_details
    })
    
    response = f"Controllable instances in AWS region:\n"
    response += "\n".join(f"• {instance}" for instance in instance_states)
    
    return response

def handle_ec2_schedule(request):
    """Handle the EC2 schedule endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    text = request.form.get('text', '').strip()
    
    # Parse text: "instance-id" or "instance-name" or "instance-id start_time to stop_time" or "instance-id clear"
    parts = text.split()
    
    if len(parts) == 1:
        # Just instance identifier - return current schedule
        instance_identifier = parts[0]
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_schedule_get", instance_identifier, {"error": "instance_not_found"}, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Get current schedule
        schedule = get_schedule(instance_id)
        
        # Get instance name for display if available
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        
        schedule_display = format_schedule_display(schedule)
        
        _log_user_action(user_id, user_name, "ec2_schedule_get", instance_id, {
            "instance_name": instance_name,
            "schedule": schedule,
            "original_identifier": instance_identifier
        })
        
        return f"Schedule for `{display_name}` ({instance_id}): {schedule_display}"
    
    elif len(parts) == 2:
        # Instance identifier and command - could be clear command or invalid format
        instance_identifier, command = parts
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_schedule_clear", instance_identifier, {
                "command": command,
                "error": "instance_not_found"
            }, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Check if this is a clear command
        if command.lower() in ALIASES_SCHEDULE_CLEAR:
            # Check if instance can be controlled by this service
            if not can_control_instance_by_id(instance_id):
                instance_name = get_instance_name(instance_id)
                display_name = instance_name if instance_name else instance_id
                _log_user_action(user_id, user_name, "ec2_schedule_clear", instance_id, {
                    "command": command,
                    "error": "instance_not_controllable",
                    "instance_name": instance_name
                }, False)
                return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
            
            # Clear the schedule
            success = delete_schedule(instance_id)
            
            # Get instance name for display if available
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            
            _log_user_action(user_id, user_name, "ec2_schedule_clear", instance_id, {
                "instance_name": instance_name,
                "command": command,
                "original_identifier": instance_identifier,
                "operation_success": success
            }, success)
            
            if success:
                response = jsonify({
                    'response_type': 'ephemeral',
                    'text': f"Schedule cleared for `{display_name}` ({instance_id})"
                })
                return response
            else:
                return f"Failed to clear schedule for `{instance_identifier}`"
        else:
            # Not a clear command, probably invalid format
            _log_user_action(user_id, user_name, "ec2_schedule", "invalid", {
                "error": "invalid_format",
                "text": text
            }, False)
            return "Usage: <instance-id|instance-name> [<start_time> to <stop_time>] or <instance-id|instance-name> clear"
    
    elif len(parts) >= 4:
        # Instance identifier and schedule - set schedule
        instance_identifier = parts[0]
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_identifier, {
                "error": "instance_not_found"
            }, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Find "to" keyword to separate start and stop times
        try:
            to_index = parts.index('to')
            if to_index < 2 or to_index >= len(parts) - 1:
                _log_user_action(user_id, user_name, "ec2_schedule", "invalid", {
                    "error": "invalid_format",
                    "text": text
                }, False)
                return "Usage: <instance-id|instance-name> <start_time> to <stop_time> or <instance-id|instance-name> clear"
            
            start_time_parts = parts[1:to_index]
            stop_time_parts = parts[to_index + 1:]
            
            start_time_str = ' '.join(start_time_parts)
            stop_time_str = ' '.join(stop_time_parts)
            
        except ValueError:
            _log_user_action(user_id, user_name, "ec2_schedule", "invalid", {
                "error": "invalid_format",
                "text": text
            }, False)
            return "Usage: <instance-id|instance-name> <start_time> to <stop_time> or <instance-id|instance-name> clear"
        
        # Parse times
        start_time = parse_time(start_time_str)
        stop_time = parse_time(stop_time_str)
        
        if not start_time:
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "error": "invalid_start_time",
                "start_time": start_time_str
            }, False)
            return f"Invalid start time: {start_time_str}"
        if not stop_time:
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "error": "invalid_stop_time",
                "stop_time": stop_time_str
            }, False)
            return f"Invalid stop time: {stop_time_str}"
        
        # Validate that start time is before end time (same-day schedules only)
        # Cross-midnight schedules are not supported due to scheduling logic complexity
        if start_time >= stop_time:
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "error": "invalid_schedule_order",
                "start_time": start_time_str,
                "stop_time": stop_time_str,
                "start_time_parsed": str(start_time),
                "stop_time_parsed": str(stop_time),
                "note": "cross_midnight_or_same_time"
            }, False)
            return f"Invalid schedule: start time ({start_time_str}) must be before end time ({stop_time_str}). Cross-midnight schedules are not supported."
        
        # Get instance name for display if available
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        
        # Check if instance can be controlled by this service
        if not can_control_instance_by_id(instance_id):
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "error": "instance_not_controllable",
                "instance_name": instance_name,
                "start_time": start_time_str,
                "stop_time": stop_time_str
            }, False)
            return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
        
        # Set the schedule
        if set_schedule(instance_id, start_time, stop_time):
            start_display = start_time.strftime('%I:%M %p').lstrip('0')
            stop_display = stop_time.strftime('%I:%M %p').lstrip('0')
            
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "instance_name": instance_name,
                "start_time": start_time_str,
                "stop_time": stop_time_str,
                "start_display": start_display,
                "stop_display": stop_display
            })
            
            response = jsonify({
                'response_type': 'ephemeral',
                'text': f"Schedule set for `{display_name}` ({instance_id}): {start_display} to {stop_display}"
            })
            return response
        else:
            _log_user_action(user_id, user_name, "ec2_schedule_set", instance_id, {
                "error": "failed_to_set_schedule"
            }, False)
            return f"Failed to set schedule for `{display_name}` ({instance_id})"
    
    else:
        _log_user_action(user_id, user_name, "ec2_schedule", "invalid", {
            "error": "invalid_format",
            "text": text
        }, False)
        return "Usage: <instance-id|instance-name> [<start_time> to <stop_time>] or <instance-id|instance-name> clear"

def handle_fuzzy_search(request):
    """Handle the fuzzy search endpoint - search controllable instances by name or ID"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    text = request.form.get('text', '').strip()
    
    if not text:
        _log_user_action(user_id, user_name, "fuzzy_search", "empty", {"error": "no_search_term"})
        return "Please provide a search term. Usage: /search <instance-name-or-id>"
    
    # Perform fuzzy search
    matching_instances = fuzzy_search_instances(text)
    
    if not matching_instances:
        _log_user_action(user_id, user_name, "fuzzy_search", text, {
            "search_term": text,
            "results_count": 0
        })
        return f"No controllable instances found matching '{text}'. Add the `EC2ControlsEnabled` tag with a truthy value to instances you want to control."
    
    # Format results
    instance_states = []
    instance_details = []
    
    for instance in matching_instances:
        instance_id = instance['InstanceId']
        instance_name = instance.get('Name')
        state = instance['State']
        
        instance_detail = {
            "instance_id": instance_id,
            "instance_name": instance_name,
            "state": state
        }
        instance_details.append(instance_detail)
        
        if instance_name:
            instance_states.append(f"`{instance_name}` ({instance_id}) - {state}")
        else:
            instance_states.append(f"`{instance_id}` - {state}")
    
    # Log the search action
    _log_user_action(user_id, user_name, "fuzzy_search", text, {
        "search_term": text,
        "results_count": len(matching_instances),
        "instances": instance_details
    })
    
    response = f"Found {len(matching_instances)} controllable instance(s) matching '{text}':\n"
    response += "\n".join(f"• {instance}" for instance in instance_states)
    
    return response

def handle_ec2_disable_schedule(request):
    """Handle the EC2 disable schedule endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    text = request.form.get('text', '').strip()
    
    # Parse text: "instance-id" or "instance-name" or "instance-id datetime" or "instance-id cancel"
    parts = text.split()
    
    if len(parts) == 1:
        # Just instance identifier - return current disable schedule status
        instance_identifier = parts[0]
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_disable_schedule_get", instance_identifier, {"error": "instance_not_found"}, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Get current disable schedule
        disable_datetime = get_disable_schedule(instance_id)
        
        # Get instance name for display if available
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        
        disable_display = format_disable_schedule_display(disable_datetime)
        
        _log_user_action(user_id, user_name, "ec2_disable_schedule_get", instance_id, {
            "instance_name": instance_name,
            "disable_datetime": disable_datetime.isoformat() if disable_datetime else None,
            "original_identifier": instance_identifier
        })
        
        return f"Scheduler for `{display_name}` ({instance_id}): {disable_display}"
    
    elif len(parts) >= 2:
        # Instance identifier and command - could be cancel command or datetime
        instance_identifier = parts[0]
        command_parts = parts[1:]
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
        if not instance_id:
            _log_user_action(user_id, user_name, "ec2_disable_schedule_cancel", instance_identifier, {
                "command": ' '.join(command_parts),
                "error": "instance_not_found"
            }, False)
            return f"Instance `{instance_identifier}` not found"
        
        # Join command parts for processing
        command = ' '.join(command_parts)
        
        # Check if this is a cancel command
        if command.lower() in ALIASES_DISABLE_CANCEL:
            # Check if instance can be controlled by this service
            if not can_control_instance_by_id(instance_id):
                instance_name = get_instance_name(instance_id)
                display_name = instance_name if instance_name else instance_id
                _log_user_action(user_id, user_name, "ec2_disable_schedule_cancel", instance_id, {
                    "command": command,
                    "error": "instance_not_controllable",
                    "instance_name": instance_name
                }, False)
                return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
            
            # Cancel the disable schedule
            success = delete_disable_schedule(instance_id)
            
            # Get instance name for display if available
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            
            _log_user_action(user_id, user_name, "ec2_disable_schedule_cancel", instance_id, {
                "instance_name": instance_name,
                "command": command,
                "original_identifier": instance_identifier,
                "operation_success": success
            }, success)
            
            if success:
                response = jsonify({
                    'response_type': 'ephemeral',
                    'text': f"Unpaused scheduler service for `{display_name}` ({instance_id})"
                })
                return response
            else:
                return f"Failed to unpause scheduler for `{instance_identifier}`"
        else:
            # Not a cancel command, treat as hours
            # Parse the hours
            hours = parse_hours(command)
            if not hours:
                _log_user_action(user_id, user_name, "ec2_disable_schedule_set", instance_id, {
                    "error": "invalid_hours",
                    "hours_str": command
                }, False)
                return f"Invalid hours format: {command}. Use format like '2h', '24h', etc. (minimum 1h)."
            
            # Check if instance can be controlled by this service
            if not can_control_instance_by_id(instance_id):
                instance_name = get_instance_name(instance_id)
                display_name = instance_name if instance_name else instance_id
                _log_user_action(user_id, user_name, "ec2_disable_schedule_set", instance_id, {
                    "error": "instance_not_controllable",
                    "instance_name": instance_name,
                    "hours": hours
                }, False)
                return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
            
            # Set the disable schedule
            success = set_disable_schedule(instance_id, hours)
            
            # Get instance name for display if available
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            
            if success:
                _log_user_action(user_id, user_name, "ec2_disable_schedule_set", instance_id, {
                    "instance_name": instance_name,
                    "hours": hours
                })
                
                response = jsonify({
                    'response_type': 'ephemeral',
                    'text': f"Paused scheduler for `{display_name}` ({instance_id}) for {hours} hours"
                })
                return response
            else:
                _log_user_action(user_id, user_name, "ec2_disable_schedule_set", instance_id, {
                    "error": "failed_to_set_disable_schedule"
                }, False)
                return f"Failed to pause scheduler for `{display_name}` ({instance_id})"
    
    else:
        _log_user_action(user_id, user_name, "ec2_disable_schedule", "invalid", {
            "error": "invalid_format",
            "text": text
        }, False)
        return "Usage: <instance-id|instance-name> [<hours>] or <instance-id|instance-name> cancel"

def handle_ec2_stakeholder(request):
    """Handle the EC2 stakeholder endpoint - allows users to claim, remove, and check stakeholder status"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    text = request.form.get('text', '').strip()
    
    # Parse text: "<instance-id|instance-name> [claim|remove|check]"
    parts = text.split()
    
    if len(parts) == 0:
        _log_user_action(user_id, user_name, "ec2_stakeholder", "invalid", {
            "error": "invalid_format",
            "text": text
        }, False)
        return "Usage: <instance-id|instance-name> [claim|remove|show]"
    
    # Handle instance-specific commands
    if len(parts) < 1 or len(parts) > 2:
        _log_user_action(user_id, user_name, "ec2_stakeholder", "invalid", {
            "error": "invalid_format",
            "text": text
        }, False)
        return "Usage: <instance-id|instance-name> [claim|remove|show]"
    
    instance_identifier = parts[0]
    action = parts[1].lower() if len(parts) == 2 else 'claim'  # Default to claim if no action specified
    # Normalize stakeholder action using aliases
    action = normalize_command(action, ACTION_ALIASES_STAKEHOLDER)
    
    # Validate action
    if action not in ['claim', 'remove', 'check']:
        _log_user_action(user_id, user_name, "ec2_stakeholder", instance_identifier, {
            "error": "invalid_action",
            "action": action
        }, False)
        return "Action must be 'claim', 'remove', or 'check'"
    
    # Resolve to instance ID
    instance_id = resolve_instance_identifier(instance_identifier)
    logger.info(f"resolve_instance_identifier('{instance_identifier}') returned: {instance_id}")
    if not instance_id:
        _log_user_action(user_id, user_name, "ec2_stakeholder", instance_identifier, {
            "error": "instance_not_found",
            "action": action
        }, False)
        return f"Instance `{instance_identifier}` not found"
    
    # Check if instance can be controlled by this service
    if not can_control_instance_by_id(instance_id):
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        _log_user_action(user_id, user_name, "ec2_stakeholder", instance_id, {
            "error": "instance_not_controllable",
            "instance_name": instance_name,
            "action": action
        }, False)
        return f"Instance `{display_name}` ({instance_id}) cannot be controlled by this service. Add the `EC2ControlsEnabled` tag with a truthy value to enable control."
    
    # Get instance name for display if available
    instance_name = get_instance_name(instance_id)
    display_name = instance_name if instance_name else instance_id
    
    # Perform the requested action
    if action == 'claim':
        success, result = add_stakeholder(instance_id, user_id)
        
        if success:
            if result == "added":
                _log_user_action(user_id, user_name, "ec2_stakeholder_claim", instance_id, {
                    "instance_name": instance_name,
                    "action": "added_stakeholder",
                    "original_identifier": instance_identifier
                })
                return f"You are now a stakeholder for `{display_name}` ({instance_id})"
            elif result == "already_stakeholder":
                _log_user_action(user_id, user_name, "ec2_stakeholder_claim", instance_id, {
                    "instance_name": instance_name,
                    "action": "already_stakeholder",
                    "original_identifier": instance_identifier
                })
                return f"You are already a stakeholder for `{display_name}` ({instance_id})"
            else:
                _log_user_action(user_id, user_name, "ec2_stakeholder_claim", instance_id, {
                    "instance_name": instance_name,
                    "action": "unknown_result",
                    "result": result,
                    "original_identifier": instance_identifier
                }, False)
                return f"Failed to claim `{display_name}` ({instance_id}) - please try again"
        else:
            if result == "max_limit_reached":
                _log_user_action(user_id, user_name, "ec2_stakeholder_claim", instance_id, {
                    "instance_name": instance_name,
                    "action": "max_limit_reached",
                    "original_identifier": instance_identifier
                }, False)
                return f"Max stakeholders (10) reached for `{display_name}` ({instance_id})"
            else:
                _log_user_action(user_id, user_name, "ec2_stakeholder_claim", instance_id, {
                    "instance_name": instance_name,
                    "action": "failed",
                    "result": result,
                    "original_identifier": instance_identifier
                }, False)
                return f"Failed to claim `{display_name}` ({instance_id}) - please try again"
    
    elif action == 'remove':
        success, result = remove_stakeholder(instance_id, user_id)
        
        if success:
            if result == "removed":
                _log_user_action(user_id, user_name, "ec2_stakeholder_remove", instance_id, {
                    "instance_name": instance_name,
                    "action": "removed_stakeholder",
                    "original_identifier": instance_identifier
                })
                return f"You are no longer a stakeholder for `{display_name}` ({instance_id})"
            elif result == "removed_and_deleted_tag":
                _log_user_action(user_id, user_name, "ec2_stakeholder_remove", instance_id, {
                    "instance_name": instance_name,
                    "action": "removed_stakeholder_and_deleted_tag",
                    "original_identifier": instance_identifier
                })
                return f"You are no longer a stakeholder for `{display_name}` ({instance_id})"
            elif result == "not_stakeholder":
                _log_user_action(user_id, user_name, "ec2_stakeholder_remove", instance_id, {
                    "instance_name": instance_name,
                    "action": "not_stakeholder",
                    "original_identifier": instance_identifier
                })
                return f"You are not a stakeholder for `{display_name}` ({instance_id})"
            else:
                _log_user_action(user_id, user_name, "ec2_stakeholder_remove", instance_id, {
                    "instance_name": instance_name,
                    "action": "unknown_result",
                    "result": result,
                    "original_identifier": instance_identifier
                }, False)
                return f"Failed to remove stakeholder status for `{display_name}` ({instance_id}) - please try again"
        else:
            _log_user_action(user_id, user_name, "ec2_stakeholder_remove", instance_id, {
                "instance_name": instance_name,
                "action": "failed",
                "result": result,
                "original_identifier": instance_identifier
            }, False)
            return f"Failed to remove stakeholder status for `{display_name}` ({instance_id}) - please try again"
    
    elif action == 'check':
        is_stakeholder = is_user_stakeholder(instance_id, user_id)
        
        if is_stakeholder:
            _log_user_action(user_id, user_name, "ec2_stakeholder_check", instance_id, {
                "instance_name": instance_name,
                "action": "is_stakeholder",
                "original_identifier": instance_identifier
            })
            return f"You are a stakeholder for `{display_name}` ({instance_id})"
        else:
            _log_user_action(user_id, user_name, "ec2_stakeholder_check", instance_id, {
                "instance_name": instance_name,
                "action": "not_stakeholder",
                "original_identifier": instance_identifier
            })
            return f"You are not a stakeholder for `{display_name}` ({instance_id})"