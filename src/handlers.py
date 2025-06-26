import logging
from flask import jsonify
from src.aws_client import get_instance_state, start_instance, stop_instance
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
            return f"Access to instance `{instance_id}` denied."
        
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
            return f"Access to instance `{instance_id}` denied."
        
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

def handle_help(request):
    """Handle the help endpoint"""
    help_text = """Available Commands:

*Admin Check:*
• `/admin/check` - Check if a user is an administrator
  Usage: POST with `user_id` and `user_name` parameters

*Instance Management:*
• `/instances` - List instances assigned to a user with their current states
  Usage: POST with `user_id` and `user_name` parameters

*EC2 Instance Control:*
• `/ec2/power` or `/ec2-power-state` - Control EC2 instance power states
  Usage: POST with `user_id` and `text` parameters
  
  Text format:
  - `<instance-id>` - Get current state of instance
  - `<instance-id> on` - Start the instance
  - `<instance-id> off` - Stop the instance
  
  Examples:
  - `i-0fff0f1804788ae88` - Check status
  - `i-0fff0f1804788ae88 on` - Start instance
  - `i-0fff0f1804788ae88 off` - Stop instance

*Health Check:*
• `/health` - Check if the service is running
  Returns: `{"status": "ok"}`

Note: You can only control instances that are assigned to your user ID."""
    
    return help_text

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
        if state:
            instance_states.append(f"`{instance_id}` - {state}")
        else:
            instance_states.append(f"`{instance_id}` - unknown state")
    
    response = f"Instances assigned to `{user_name}`:\n"
    response += "\n".join(f"• {instance}" for instance in instance_states)
    
    return response