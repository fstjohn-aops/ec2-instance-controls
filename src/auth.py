from src.aws_client import get_all_instances

def get_user_instances(user_id):
    """Get list of all instances - returns all instances for any user"""
    # Get all instances from AWS
    instances = get_all_instances()
    return [instance['InstanceId'] for instance in instances] if instances else [] 