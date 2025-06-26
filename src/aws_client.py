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
    logger.info(f"get_instance_state called with instance_id: {instance_id}")
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

def get_instance_by_name(instance_name):
    """Find an EC2 instance by its Name tag"""
    try:
        logger.info(f"Searching for instance with Name tag: {instance_name}")
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [instance_name]
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['pending', 'running', 'stopping', 'stopped']
                }
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance)
        
        logger.info(f"Found {len(instances)} instances with name '{instance_name}'")
        
        if len(instances) == 1:
            instance_id = instances[0]['InstanceId']
            logger.info(f"Returning single instance: {instance_id}")
            return instances[0]
        elif len(instances) > 1:
            instance_ids = [i['InstanceId'] for i in instances]
            logger.warning(f"Multiple instances found with name '{instance_name}': {instance_ids}")
            return None
        else:
            logger.warning(f"No instances found with name '{instance_name}'")
            return None
    except Exception as e:
        logger.error(f"AWS Error finding instance by name '{instance_name}': {e}")
        return None

def get_instance_details(instance_id):
    """Get detailed information about an EC2 instance including Name tag"""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            return instance
        return None
    except Exception as e:
        logger.error(f"AWS Error getting instance details: {e}")
        return None

def get_instance_name(instance_id):
    """Get the Name tag of an EC2 instance"""
    instance = get_instance_details(instance_id)
    if instance and 'Tags' in instance:
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                return tag['Value']
    return None

def resolve_instance_identifier(identifier):
    """Resolve an instance identifier (ID or Name) to instance ID"""
    logger.info(f"Resolving instance identifier: {identifier}")
    
    # If it looks like an instance ID, return it directly
    if identifier.startswith('i-'):
        logger.info(f"Identifier '{identifier}' looks like an instance ID, returning directly")
        return identifier
    
    # Otherwise, treat it as a Name tag
    logger.info(f"Treating '{identifier}' as instance name, looking up by Name tag")
    instance = get_instance_by_name(identifier)
    if instance:
        instance_id = instance['InstanceId']
        logger.info(f"Found instance '{identifier}' with ID: {instance_id}")
        return instance_id
    else:
        logger.warning(f"No instance found with name: {identifier}")
        return None