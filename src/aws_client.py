import boto3
import logging
import os
from src.config import AWS_REGION

logger = logging.getLogger(__name__)

# Get credentials from environment variables
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
aws_region = os.environ.get('AWS_REGION', AWS_REGION)

# Initialize AWS client with explicit credentials
if aws_access_key_id and aws_secret_access_key:
    ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    logger.info(f"AWS client initialized with explicit credentials for region: {aws_region}")
else:
    # Fallback to default credential chain (instance role, etc.)
    ec2_client = boto3.client('ec2', region_name=aws_region)
    logger.warning("AWS credentials not found in environment variables, using default credential chain")

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