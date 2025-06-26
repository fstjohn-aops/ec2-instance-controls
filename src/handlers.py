import logging
from flask import jsonify
from src.aws_client import get_instance_state, start_instance, stop_instance
from src.auth import is_admin, can_control_instance

logger = logging.getLogger(__name__)

def handle_admin_check(request):
    """Handle the admin check endpoint"""
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    
    if is_admin(user_id):
        return f"User: `{user_name}` is an administrator."
    else:
        return f"User: `{user_name}` is not an administrator."

def handle_ec2_power(request):
    """Handle the EC2 power control endpoint"""
    user_id = request.form.get('user_id', '')
    text = request.form.get('text', '').strip()
    
    # Parse text: "i-0df9c53001c5c837d" or "i-0df9c53001c5c837d on"
    parts = text.split()
    
    if len(parts) == 1:
        # Just instance ID - return current state
        instance_id = parts[0]
        
        if not can_control_instance(user_id, instance_id):
            return f"access to instance `{instance_id}` denied"
        
        # Get current state
        current_state = get_instance_state(instance_id)
        if current_state:
            return f"Instance `{instance_id}` is currently {current_state}"
        else:
            return f"Instance `{instance_id}` not found"
    
    elif len(parts) == 2:
        # Instance ID and power state - change state
        instance_id, power_state = parts
        
        if not can_control_instance(user_id, instance_id):
            return f"access to instance `{instance_id}` denied"
        
        if power_state not in ['on', 'off']:
            return "Power state must be 'on' or 'off'."
        
        # Respond immediately
        response = jsonify({
            'response_type': 'ephemeral',
            'text': f"Set `{instance_id}` to {power_state}"
        })
        
        # Then do the AWS operation
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
        return "Usage: <instance-id> [on|off]"