from src.aws_client import get_controllable_instances

def get_all_region_instances():
    """Get list of all instances in the AWS region that can be controlled by this service"""
    # Get only controllable instances from AWS
    instances = get_controllable_instances()
    return [instance['InstanceId'] for instance in instances] if instances else [] 