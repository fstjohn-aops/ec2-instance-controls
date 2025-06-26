from src.config import ADMIN_USERS, USER_INSTANCES
from src.aws_client import resolve_instance_identifier

def is_admin(user_id):
    """Check if user is an administrator"""
    return user_id in ADMIN_USERS

def can_control_instance(user_id, instance_identifier):
    """Check if user can control the specified instance (by ID or Name)"""
    # Admins can control any instance
    if is_admin(user_id):
        return True
    
    # Resolve instance identifier to instance ID
    instance_id = resolve_instance_identifier(instance_identifier)
    if not instance_id:
        return False
    
    # Regular users can only control their assigned instances
    return user_id in USER_INSTANCES and instance_id in USER_INSTANCES[user_id]

def get_user_instances(user_id):
    """Get list of instances a user can control"""
    return USER_INSTANCES.get(user_id, []) 