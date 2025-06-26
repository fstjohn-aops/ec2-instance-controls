import logging
import re
from flask import jsonify
from src.aws_client import get_instance_state, start_instance, stop_instance, resolve_instance_identifier, get_instance_name
from src.auth import is_admin, can_control_instance, get_user_instances

logger = logging.getLogger(__name__)

def handle_admin_check(request):
    """Handle the admin check endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    
    if is_admin(user_id):
        return f"User: `{user_name}` is an administrator."
    else:
        return f"User: `{user_name}` is not an administrator."

def _is_valid_instance_id(instance_id):
    """Validate EC2 instance ID format"""
    # EC2 instance IDs follow pattern: i- followed by 8 or 17 hex characters
    pattern = r'^i-[0-9a-f]{8}$|^i-[0-9a-f]{17}$'
    return bool(re.match(pattern, instance_id))

def handle_ec2_power(request):
    """Handle the EC2 power control endpoint"""
    user_id = request.form.get('user_id', '')
    text = request.form.get('text', '').strip()
    
    # Parse text: "instance-id" or "instance-name" or "instance-id on" or "instance-name on"
    parts = text.split()
    
    if len(parts) == 1:
        # Just instance identifier - return current state
        instance_identifier = parts[0]
        
        # Check if user can control this instance
        if not can_control_instance(user_id, instance_identifier):
            return f"Access to instance `{instance_identifier}` denied."
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        if not instance_id:
            return f"Instance `{instance_identifier}` not found"
        
        # Get current state using the resolved instance ID
        logger.info(f"Calling get_instance_state with resolved instance_id: {instance_id}")
        current_state = get_instance_state(instance_id)
        if current_state:
            # Get instance name for display if available
            instance_name = get_instance_name(instance_id)
            display_name = instance_name if instance_name else instance_id
            return f"Instance `{display_name}` ({instance_id}) is currently {current_state}"
        else:
            return f"Instance `{instance_identifier}` not found"
    
    elif len(parts) == 2:
        # Instance identifier and power state - change state
        instance_identifier, power_state = parts
        
        # Check if user can control this instance
        if not can_control_instance(user_id, instance_identifier):
            return f"Access to instance `{instance_identifier}` denied."
        
        # Resolve to instance ID
        instance_id = resolve_instance_identifier(instance_identifier)
        if not instance_id:
            return f"Instance `{instance_identifier}` not found"
        
        if power_state not in ['on', 'off']:
            return "Power state must be 'on' or 'off'."
        
        # Get instance name for display if available
        instance_name = get_instance_name(instance_id)
        display_name = instance_name if instance_name else instance_id
        
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
                start_instance(instance_id)
            else:
                stop_instance(instance_id)
        else:
            logger.error(f"AWS: Instance `{instance_id}` not found")
        
        return response
    
    else:
        return "Usage: <instance-id|instance-name> [on|off]"

def handle_list_instances(request):
    """Handle the list instances endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    
    if not user_id:
        return "Error: user_id parameter is required."
    
    instances = get_user_instances(user_id)
    
    if not instances:
        return f"User `{user_name}` has no assigned instances."
    
    # Get current state for each instance
    instance_states = []
    for instance_id in instances:
        state = get_instance_state(instance_id)
        instance_name = get_instance_name(instance_id)
        
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
    
    response = f"Instances assigned to `{user_name}`:\n"
    response += "\n".join(f"• {instance}" for instance in instance_states)
    
    return response