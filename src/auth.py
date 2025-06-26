from src.config import ADMIN_USERS, USER_INSTANCES

def is_admin(user_id):
    """Check if user is an administrator"""
    return user_id in ADMIN_USERS

def can_control_instance(user_id, instance_id):
    """Check if user can control the specified instance"""
    return user_id in USER_INSTANCES and instance_id in USER_INSTANCES[user_id]

def get_user_instances(user_id):
    """Get list of instances a user can control"""
    return USER_INSTANCES.get(user_id, []) 