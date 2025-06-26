import boto3
import logging
import os
import json
from datetime import datetime, timezone
from src.config import AWS_REGION

logger = logging.getLogger(__name__)

# Get AWS region from environment variable
aws_region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS EC2 client
try:
    ec2_client = boto3.client('ec2')
    logger.info("AWS credentials found in environment variables")
except Exception as e:
    logger.error(f"Failed to initialize AWS client: {e}")
    raise

def _log_aws_operation(operation, target, details=None, success=True, error=None):
    """Log AWS operations for auditing purposes"""
    timestamp = datetime.now(timezone.utc).isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_entry = {
        'timestamp': timestamp,
        'aws_operation': operation,
        'target': target,
        'region': aws_region,
        'details': details,
        'status': status,
        'pod_name': os.environ.get('HOSTNAME', 'unknown'),
        'namespace': os.environ.get('POD_NAMESPACE', 'unknown')
    }
    if error:
        log_entry['error'] = str(error)
    
    logger.info(f"AWS_AUDIT: {json.dumps(log_entry)}")

def get_instance_state(instance_id):
    """Get the current state of an EC2 instance"""
    logger.info(f"get_instance_state called with instance_id: {instance_id}")
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            state = instance['State']['Name']
            _log_aws_operation("describe_instances", instance_id, {
                "instance_state": state,
                "instance_type": instance.get('InstanceType'),
                "launch_time": instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None
            })
            return state
        _log_aws_operation("describe_instances", instance_id, {"error": "no_reservations_found"}, False)
        return None
    except Exception as e:
        logger.error(f"AWS Error getting instance state: {e}")
        _log_aws_operation("describe_instances", instance_id, {"error": str(e)}, False, e)
        return None

def start_instance(instance_id):
    """Start an EC2 instance"""
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        logger.info(f"AWS: Started {instance_id}")
        _log_aws_operation("start_instances", instance_id, {
            "previous_state": response['StartingInstances'][0]['PreviousState']['Name'],
            "current_state": response['StartingInstances'][0]['CurrentState']['Name']
        })
        return True
    except Exception as e:
        logger.error(f"AWS Error starting instance: {e}")
        _log_aws_operation("start_instances", instance_id, {"error": str(e)}, False, e)
        return False

def stop_instance(instance_id):
    """Stop an EC2 instance"""
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        logger.info(f"AWS: Stopped {instance_id}")
        _log_aws_operation("stop_instances", instance_id, {
            "previous_state": response['StoppingInstances'][0]['PreviousState']['Name'],
            "current_state": response['StoppingInstances'][0]['CurrentState']['Name']
        })
        return True
    except Exception as e:
        logger.error(f"AWS Error stopping instance: {e}")
        _log_aws_operation("stop_instances", instance_id, {"error": str(e)}, False, e)
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
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "found_instance_id": instance_id,
                "instance_count": 1
            })
            return instance_id
        elif len(instances) > 1:
            instance_ids = [i['InstanceId'] for i in instances]
            logger.warning(f"Multiple instances found with name '{instance_name}': {instance_ids}")
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "error": "multiple_instances_found",
                "instance_ids": instance_ids
            }, False)
            return None
        else:
            logger.warning(f"No instances found with name '{instance_name}'")
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "error": "no_instances_found"
            }, False)
            return None
    except Exception as e:
        logger.error(f"AWS Error finding instance by name '{instance_name}': {e}")
        _log_aws_operation("describe_instances_by_name", instance_name, {"error": str(e)}, False, e)
        return None

def get_instance_details(instance_id):
    """Get detailed information about an EC2 instance including Name tag"""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            _log_aws_operation("describe_instances_details", instance_id, {
                "instance_type": instance.get('InstanceType'),
                "launch_time": instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                "state": instance['State']['Name']
            })
            return instance
        _log_aws_operation("describe_instances_details", instance_id, {"error": "no_reservations_found"}, False)
        return None
    except Exception as e:
        logger.error(f"AWS Error getting instance details: {e}")
        _log_aws_operation("describe_instances_details", instance_id, {"error": str(e)}, False, e)
        return None

def get_instance_name(instance_id):
    """Get the Name tag of an EC2 instance"""
    instance = get_instance_details(instance_id)
    if instance and 'Tags' in instance:
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                return tag['Value']
    return None

def get_all_instances():
    """Get all EC2 instances in the region"""
    try:
        response = ec2_client.describe_instances(
            Filters=[
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
        
        logger.info(f"Found {len(instances)} instances in region {aws_region}")
        _log_aws_operation("describe_instances_all", "all", {
            "instance_count": len(instances),
            "instance_ids": [i['InstanceId'] for i in instances]
        })
        return instances
    except Exception as e:
        logger.error(f"AWS Error getting all instances: {e}")
        _log_aws_operation("describe_instances_all", "all", {"error": str(e)}, False, e)
        return []

def resolve_instance_identifier(identifier):
    """Resolve an instance identifier (ID or Name) to instance ID"""
    logger.info(f"Resolving instance identifier: {identifier}")
    
    # If it looks like an instance ID, return it directly
    if identifier.startswith('i-'):
        logger.info(f"Identifier '{identifier}' looks like an instance ID, returning directly")
        return identifier
    
    # Otherwise, treat it as a Name tag
    logger.info(f"Treating '{identifier}' as instance name, looking up by Name tag")
    instance_id = get_instance_by_name(identifier)
    logger.info(f"get_instance_by_name('{identifier}') returned: {instance_id}")
    if instance_id:
        logger.info(f"Found instance '{identifier}' with ID: {instance_id}")
        return instance_id
    else:
        logger.warning(f"No instance found with name: {identifier}")
        return None