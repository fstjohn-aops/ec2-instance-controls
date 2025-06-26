from src.aws_client import get_all_instances

def can_control_instance(user_id, instance_identifier):
    """Check if user can control the specified instance - now allows any authenticated user"""
    # Any user with a user_id can control any instance
    return bool(user_id)

def get_user_instances(user_id):
    """Get list of all instances - now returns all instances for any authenticated user"""
    if not user_id:
        return []
    
    # Get all instances from AWS
    instances = get_all_instances()
    return [instance['InstanceId'] for instance in instances] if instances else [] 