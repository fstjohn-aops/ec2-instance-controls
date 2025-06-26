import boto3
import logging
from src.config import AWS_REGION

logger = logging.getLogger(__name__)

# Initialize AWS client
ec2_client = boto3.client('ec2', region_name=AWS_REGION)

def get_instance_state(instance_id):
    """Get the current state of an EC2 instance"""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            return instance['State']['Name']
        return None
    except Exception as e:
        logger.error(f"AWS Error getting instance state: {e}")
        return None

def start_instance(instance_id):
    """Start an EC2 instance"""
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        logger.info(f"AWS: Started {instance_id}")
        return True
    except Exception as e:
        logger.error(f"AWS Error starting instance: {e}")
        return False

def stop_instance(instance_id):
    """Stop an EC2 instance"""
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        logger.info(f"AWS: Stopped {instance_id}")
        return True
    except Exception as e:
        logger.error(f"AWS Error stopping instance: {e}")
        return False 