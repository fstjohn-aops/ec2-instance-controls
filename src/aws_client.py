import boto3 # type: ignore
import logging
import os
import json
from datetime import datetime, timezone
from src.config import AWS_REGION

logger = logging.getLogger(__name__)

# Get AWS region from environment variable
aws_region = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS EC2 client - defer until needed
_ec2_client = None

def _parse_aws_error_message(error_str):
    """Parse AWS error messages to extract meaningful information for user feedback"""
    if not error_str:
        return "Unknown AWS error"
    
    # Common AWS error patterns
    if "IncorrectInstanceState" in error_str:
        if "not in a state from which it can be started" in error_str:
            return "instance_cannot_start_from_current_state"
        elif "not in a state from which it can be stopped" in error_str:
            return "instance_cannot_stop_from_current_state"
        else:
            return "incorrect_instance_state"
    elif "InvalidInstanceID" in error_str:
        return "invalid_instance_id"
    elif "UnauthorizedOperation" in error_str:
        return "unauthorized_operation"
    elif "RequestLimitExceeded" in error_str:
        return "rate_limit_exceeded"
    elif "InsufficientInstanceCapacity" in error_str:
        return "insufficient_capacity"
    elif "Unsupported" in error_str:
        return "unsupported_operation"
    else:
        return "aws_error"

def _get_ec2_client():
    """Get or create the EC2 client with proper region configuration"""

    global _ec2_client
    if _ec2_client is None:
        try:
            _ec2_client = boto3.client('ec2', region_name=aws_region)
            logger.info(f"AWS credentials found in environment variables, using region: {aws_region}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            raise
    return _ec2_client

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
        response = _get_ec2_client().describe_instances(InstanceIds=[instance_id])
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

def can_control_instance_by_id(instance_id):
    """Check if a specific instance can be controlled by this service"""
    try:
        instance = get_instance_details(instance_id)
        if not instance:
            logger.warning(f"Cannot control instance {instance_id}: instance not found")
            return False
        
        can_control = can_control_instance(instance)
        if not can_control:
            logger.warning(f"Cannot control instance {instance_id}: EC2ControlsEnabled tag not set to truthy value")
        
        return can_control
    except Exception as e:
        logger.error(f"Error checking if instance {instance_id} can be controlled: {e}")
        return False

def start_instance(instance_id):
    """Start an EC2 instance"""
    # Check if instance can be controlled before starting
    if not can_control_instance_by_id(instance_id):
        logger.error(f"Cannot start instance {instance_id}: not authorized to control this instance")
        _log_aws_operation("start_instances", instance_id, {"error": "instance_not_controllable"}, False)
        return False
    
    # Check current state before attempting start
    current_state = get_instance_state(instance_id)
    if current_state is None:
        logger.error(f"Cannot start instance {instance_id}: unable to determine current state")
        _log_aws_operation("start_instances", instance_id, {"error": "state_unknown"}, False)
        return False
    
    # Validate that instance can be started from current state
    if current_state == 'running':
        logger.error(f"Cannot start instance {instance_id}: instance is already running")
        _log_aws_operation("start_instances", instance_id, {"error": "already_running", "current_state": current_state}, False)
        return False
    elif current_state == 'pending':
        logger.error(f"Cannot start instance {instance_id}: instance is already starting (pending)")
        _log_aws_operation("start_instances", instance_id, {"error": "already_starting", "current_state": current_state}, False)
        return False
    elif current_state == 'stopping':
        logger.error(f"Cannot start instance {instance_id}: instance is currently stopping")
        _log_aws_operation("start_instances", instance_id, {"error": "currently_stopping", "current_state": current_state}, False)
        return False
    elif current_state not in ['stopped']:
        logger.error(f"Cannot start instance {instance_id}: instance is in invalid state '{current_state}' for starting")
        _log_aws_operation("start_instances", instance_id, {"error": "invalid_state_for_start", "current_state": current_state}, False)
        return False
    
    try:
        response = _get_ec2_client().start_instances(InstanceIds=[instance_id])
        instance_name = get_instance_name(instance_id)
        display_name = f"{instance_name} ({instance_id})" if instance_name else f"unnamed ({instance_id})"
        logger.info(f"AWS: Started {display_name}")
        _log_aws_operation("start_instances", instance_id, {
            "previous_state": response['StartingInstances'][0]['PreviousState']['Name'],
            "current_state": response['StartingInstances'][0]['CurrentState']['Name']
        })
        return True
    except Exception as e:
        error_type = _parse_aws_error_message(str(e))
        logger.error(f"AWS Error starting instance: {e}")
        _log_aws_operation("start_instances", instance_id, {
            "error": str(e),
            "error_type": error_type
        }, False, e)
        return False

def stop_instance(instance_id):
    """Stop an EC2 instance"""
    # Check if instance can be controlled before stopping
    if not can_control_instance_by_id(instance_id):
        logger.error(f"Cannot stop instance {instance_id}: not authorized to control this instance")
        _log_aws_operation("stop_instances", instance_id, {"error": "instance_not_controllable"}, False)
        return False
    
    # Check current state before attempting stop
    current_state = get_instance_state(instance_id)
    if current_state is None:
        logger.error(f"Cannot stop instance {instance_id}: unable to determine current state")
        _log_aws_operation("stop_instances", instance_id, {"error": "state_unknown"}, False)
        return False
    
    # Validate that instance can be stopped from current state
    if current_state == 'stopped':
        logger.error(f"Cannot stop instance {instance_id}: instance is already stopped")
        _log_aws_operation("stop_instances", instance_id, {"error": "already_stopped", "current_state": current_state}, False)
        return False
    elif current_state == 'stopping':
        logger.error(f"Cannot stop instance {instance_id}: instance is already stopping")
        _log_aws_operation("stop_instances", instance_id, {"error": "already_stopping", "current_state": current_state}, False)
        return False
    elif current_state == 'pending':
        logger.error(f"Cannot stop instance {instance_id}: instance is currently starting (pending)")
        _log_aws_operation("stop_instances", instance_id, {"error": "currently_starting", "current_state": current_state}, False)
        return False
    elif current_state not in ['running']:
        logger.error(f"Cannot stop instance {instance_id}: instance is in invalid state '{current_state}' for stopping")
        _log_aws_operation("stop_instances", instance_id, {"error": "invalid_state_for_stop", "current_state": current_state}, False)
        return False
    
    try:
        response = _get_ec2_client().stop_instances(InstanceIds=[instance_id])
        instance_name = get_instance_name(instance_id)
        display_name = f"{instance_name} ({instance_id})" if instance_name else f"unnamed ({instance_id})"
        logger.info(f"AWS: Stopped {display_name}")
        _log_aws_operation("stop_instances", instance_id, {
            "previous_state": response['StoppingInstances'][0]['PreviousState']['Name'],
            "current_state": response['StoppingInstances'][0]['CurrentState']['Name']
        })
        return True
    except Exception as e:
        error_type = _parse_aws_error_message(str(e))
        logger.error(f"AWS Error stopping instance: {e}")
        _log_aws_operation("stop_instances", instance_id, {
            "error": str(e),
            "error_type": error_type
        }, False, e)
        return False

def restart_instance(instance_id):
    """Restart an EC2 instance"""
    # Check if instance can be controlled before restarting
    if not can_control_instance_by_id(instance_id):
        logger.error(f"Cannot restart instance {instance_id}: not authorized to control this instance")
        _log_aws_operation("reboot_instances", instance_id, {"error": "instance_not_controllable"}, False)
        return False
    
    # Check current state before attempting restart
    current_state = get_instance_state(instance_id)
    if current_state is None:
        logger.error(f"Cannot restart instance {instance_id}: unable to determine current state")
        _log_aws_operation("reboot_instances", instance_id, {"error": "state_unknown"}, False)
        return False
    
    # Validate that instance can be restarted from current state
    if current_state == 'stopped':
        logger.error(f"Cannot restart instance {instance_id}: instance is currently stopped")
        _log_aws_operation("reboot_instances", instance_id, {"error": "instance_stopped", "current_state": current_state}, False)
        return False
    elif current_state == 'pending':
        logger.error(f"Cannot restart instance {instance_id}: instance is currently starting (pending)")
        _log_aws_operation("reboot_instances", instance_id, {"error": "currently_starting", "current_state": current_state}, False)
        return False
    elif current_state == 'stopping':
        logger.error(f"Cannot restart instance {instance_id}: instance is currently stopping")
        _log_aws_operation("reboot_instances", instance_id, {"error": "currently_stopping", "current_state": current_state}, False)
        return False
    elif current_state not in ['running']:
        logger.error(f"Cannot restart instance {instance_id}: instance is in invalid state '{current_state}' for restarting")
        _log_aws_operation("reboot_instances", instance_id, {"error": "invalid_state_for_restart", "current_state": current_state}, False)
        return False
    
    try:
        response = _get_ec2_client().reboot_instances(InstanceIds=[instance_id])
        instance_name = get_instance_name(instance_id)
        display_name = f"{instance_name} ({instance_id})" if instance_name else f"unnamed ({instance_id})"
        logger.info(f"AWS: Restarted {display_name}")
        _log_aws_operation("reboot_instances", instance_id, {
            "operation": "reboot_requested"
        })
        return True
    except Exception as e:
        error_type = _parse_aws_error_message(str(e))
        logger.error(f"AWS Error restarting instance: {e}")
        _log_aws_operation("reboot_instances", instance_id, {
            "error": str(e),
            "error_type": error_type
        }, False, e)
        return False

def get_instance_by_name(instance_name):
    """Find an EC2 instance by its Name tag - only returns controllable instances"""
    try:
        logger.info(f"Searching for controllable instance with Name tag: {instance_name}")
        response = _get_ec2_client().describe_instances(
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
                # Only include instances that can be controlled
                if can_control_instance(instance):
                    instances.append(instance)
        
        logger.info(f"Found {len(instances)} controllable instances with name '{instance_name}'")
        
        if len(instances) == 1:
            instance_id = instances[0]['InstanceId']
            logger.info(f"Returning single controllable instance: {instance_id}")
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "found_instance_id": instance_id,
                "instance_count": 1
            })
            return instance_id
        elif len(instances) > 1:
            instance_ids = [i['InstanceId'] for i in instances]
            logger.warning(f"Multiple controllable instances found with name '{instance_name}': {instance_ids}")
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "error": "multiple_controllable_instances_found",
                "instance_ids": instance_ids
            }, False)
            return None
        else:
            logger.warning(f"No controllable instances found with name '{instance_name}'")
            _log_aws_operation("describe_instances_by_name", instance_name, {
                "error": "no_controllable_instances_found"
            }, False)
            return None
    except Exception as e:
        logger.error(f"AWS Error finding controllable instance by name '{instance_name}': {e}")
        _log_aws_operation("describe_instances_by_name", instance_name, {"error": str(e)}, False, e)
        return None

def get_instance_details(instance_id):
    """Get detailed information about an EC2 instance including Name tag"""
    try:
        response = _get_ec2_client().describe_instances(InstanceIds=[instance_id])
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

def can_control_instance(instance):
    """Check if an instance can be controlled by this service based on EC2ControlsEnabled tag"""
    if not instance or 'Tags' not in instance:
        return False
    
    for tag in instance['Tags']:
        if tag['Key'] == 'EC2ControlsEnabled':
            # Any truthy value allows control
            tag_value = tag['Value']
            if tag_value and str(tag_value).lower() not in ['false', '0', 'no', 'disabled', 'off']:
                return True
            return False
    
    # No EC2ControlsEnabled tag found - assume false (secure by default)
    return False

def get_all_instances():
    """Get all EC2 instances in the region"""
    try:
        response = _get_ec2_client().describe_instances(
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

def get_controllable_instances():
    """Get all EC2 instances that can be controlled by this service"""
    try:
        all_instances = get_all_instances()
        controllable_instances = [instance for instance in all_instances if can_control_instance(instance)]
        
        logger.info(f"Found {len(controllable_instances)} controllable instances out of {len(all_instances)} total instances")
        _log_aws_operation("describe_controllable_instances", "all", {
            "total_instances": len(all_instances),
            "controllable_instances": len(controllable_instances),
            "controllable_instance_ids": [i['InstanceId'] for i in controllable_instances]
        })
        return controllable_instances
    except Exception as e:
        logger.error(f"AWS Error getting controllable instances: {e}")
        _log_aws_operation("describe_controllable_instances", "all", {"error": str(e)}, False, e)
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

def fuzzy_search_instances(search_term):
    """Search for EC2 instances by name or ID using fuzzy matching - only returns controllable instances"""
    try:
        logger.info(f"Performing fuzzy search for: {search_term}")
        
        # Get only controllable instances
        instances = get_controllable_instances()
        
        # Perform fuzzy matching
        matching_instances = []
        search_term_lower = search_term.lower()
        
        for instance in instances:
            instance_id = instance['InstanceId']
            instance_name = None
            
            # Get instance name from tags
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break
            
            # Check if search term matches instance ID (exact or partial)
            if search_term_lower in instance_id.lower():
                matching_instances.append({
                    'InstanceId': instance_id,
                    'Name': instance_name,
                    'State': instance['State']['Name']
                })
                continue
            
            # Check if search term matches instance name (exact or partial)
            if instance_name and search_term_lower in instance_name.lower():
                matching_instances.append({
                    'InstanceId': instance_id,
                    'Name': instance_name,
                    'State': instance['State']['Name']
                })
                continue
        
        # Sort results: exact matches first, then by name, then by ID
        def sort_key(instance):
            instance_id = instance['InstanceId'].lower()
            instance_name = (instance['Name'] or '').lower()
            
            # Exact matches get highest priority
            if search_term_lower == instance_id or search_term_lower == instance_name:
                return (0, instance_name, instance_id)
            
            # Starts with search term gets second priority
            if instance_id.startswith(search_term_lower) or instance_name.startswith(search_term_lower):
                return (1, instance_name, instance_id)
            
            # Contains search term gets third priority
            return (2, instance_name, instance_id)
        
        matching_instances.sort(key=sort_key)
        
        # Limit results to prevent overwhelming responses
        max_results = 10
        if len(matching_instances) > max_results:
            matching_instances = matching_instances[:max_results]
            logger.info(f"Limited results to {max_results} instances")
        
        logger.info(f"Found {len(matching_instances)} controllable instances matching '{search_term}'")
        _log_aws_operation("fuzzy_search_instances", search_term, {
            "search_term": search_term,
            "results_count": len(matching_instances),
            "instance_ids": [i['InstanceId'] for i in matching_instances]
        })
        
        return matching_instances
        
    except Exception as e:
        logger.error(f"AWS Error performing fuzzy search for '{search_term}': {e}")
        _log_aws_operation("fuzzy_search_instances", search_term, {"error": str(e)}, False, e)
        return []

def get_instance_tags(instance_id):
    """Get all tags for an EC2 instance"""
    try:
        response = _get_ec2_client().describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            tags = instance.get('Tags', [])
            _log_aws_operation("get_instance_tags", instance_id, {
                "tag_count": len(tags),
                "tag_keys": [tag['Key'] for tag in tags]
            })
            return tags
        _log_aws_operation("get_instance_tags", instance_id, {"error": "no_reservations_found"}, False)
        return []
    except Exception as e:
        logger.error(f"AWS Error getting instance tags: {e}")
        _log_aws_operation("get_instance_tags", instance_id, {"error": str(e)}, False, e)
        return []

def get_power_schedule_tags(instance_id):
    """Get power schedule tags for an EC2 instance"""
    tags = get_instance_tags(instance_id)
    schedule_tags = {}
    
    for tag in tags:
        if tag['Key'] == 'PowerScheduleOnTime':
            schedule_tags['on_time'] = tag['Value']
        elif tag['Key'] == 'PowerScheduleOffTime':
            schedule_tags['off_time'] = tag['Value']
    
    _log_aws_operation("get_power_schedule_tags", instance_id, {
        "schedule_tags_found": schedule_tags
    })
    return schedule_tags

def set_power_schedule_tags(instance_id, on_time=None, off_time=None):
    """Set power schedule tags for an EC2 instance"""
    try:
        tags_to_set = []
        
        if on_time is not None:
            tags_to_set.append({
                'Key': 'PowerScheduleOnTime',
                'Value': on_time
            })
        
        if off_time is not None:
            tags_to_set.append({
                'Key': 'PowerScheduleOffTime',
                'Value': off_time
            })
        
        if not tags_to_set:
            logger.warning(f"No tags to set for instance {instance_id}")
            return False
        
        response = _get_ec2_client().create_tags(
            Resources=[instance_id],
            Tags=tags_to_set
        )
        
        logger.info(f"Successfully set power schedule tags for {instance_id}: {tags_to_set}")
        _log_aws_operation("set_power_schedule_tags", instance_id, {
            "tags_set": [tag['Key'] for tag in tags_to_set],
            "on_time": on_time,
            "off_time": off_time
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error setting power schedule tags for {instance_id}: {e}")
        _log_aws_operation("set_power_schedule_tags", instance_id, {
            "error": str(e),
            "on_time": on_time,
            "off_time": off_time
        }, False, e)
        return False

def delete_power_schedule_tags(instance_id):
    """Delete power schedule tags for an EC2 instance"""
    try:
        response = _get_ec2_client().delete_tags(
            Resources=[instance_id],
            Tags=[
                {'Key': 'PowerScheduleOnTime'},
                {'Key': 'PowerScheduleOffTime'}
            ]
        )
        
        logger.info(f"Successfully deleted power schedule tags for {instance_id}")
        _log_aws_operation("delete_power_schedule_tags", instance_id, {
            "tags_deleted": ["PowerScheduleOnTime", "PowerScheduleOffTime"]
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error deleting power schedule tags for {instance_id}: {e}")
        _log_aws_operation("delete_power_schedule_tags", instance_id, {
            "error": str(e)
        }, False, e)
        return False

def get_disable_schedule_tag(instance_id):
    """Get disable schedule tag for an EC2 instance"""
    tags = get_instance_tags(instance_id)
    
    for tag in tags:
        if tag['Key'] == 'PowerScheduleDisabledUntil':
            _log_aws_operation("get_disable_schedule_tag", instance_id, {
                "disable_schedule_tag_found": tag['Value']
            })
            return tag['Value']
    
    _log_aws_operation("get_disable_schedule_tag", instance_id, {
        "disable_schedule_tag_found": False
    })
    return None

def set_disable_schedule_tag(instance_id, disable_until=None):
    """Set disable schedule tag for an EC2 instance"""
    try:
        tags_to_set = []
        
        if disable_until is not None:
            tags_to_set.append({
                'Key': 'PowerScheduleDisabledUntil',
                'Value': disable_until
            })
        
        if not tags_to_set:
            logger.warning(f"No tags to set for instance {instance_id}")
            return False
        
        response = _get_ec2_client().create_tags(
            Resources=[instance_id],
            Tags=tags_to_set
        )
        
        logger.info(f"Successfully set disable schedule tag for {instance_id}: {tags_to_set}")
        _log_aws_operation("set_disable_schedule_tag", instance_id, {
            "tags_set": [tag['Key'] for tag in tags_to_set],
            "disable_until": disable_until
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error setting disable schedule tag for {instance_id}: {e}")
        _log_aws_operation("set_disable_schedule_tag", instance_id, {
            "error": str(e),
            "disable_until": disable_until
        }, False, e)
        return False

def delete_disable_schedule_tag(instance_id):
    """Delete disable schedule tag for an EC2 instance"""
    try:
        response = _get_ec2_client().delete_tags(
            Resources=[instance_id],
            Tags=[
                {'Key': 'PowerScheduleDisabledUntil'}
            ]
        )
        
        logger.info(f"Successfully deleted disable schedule tag for {instance_id}")
        _log_aws_operation("delete_disable_schedule_tag", instance_id, {
            "tags_deleted": ["PowerScheduleDisabledUntil"]
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error deleting disable schedule tag for {instance_id}: {e}")
        _log_aws_operation("delete_disable_schedule_tag", instance_id, {
            "error": str(e)
        }, False, e)
        return False

def get_stakeholders_tag(instance_id):
    """Get stakeholders tag for an EC2 instance"""
    tags = get_instance_tags(instance_id)
    
    for tag in tags:
        if tag['Key'] == 'Stakeholders':
            _log_aws_operation("get_stakeholders_tag", instance_id, {
                "stakeholders_tag_found": tag['Value']
            })
            return tag['Value']
    
    _log_aws_operation("get_stakeholders_tag", instance_id, {
        "stakeholders_tag_found": False
    })
    return None

def set_stakeholders_tag(instance_id, stakeholders_list):
    """Set stakeholders tag for an EC2 instance"""
    try:
        # Convert list to comma-separated string
        stakeholders_str = ','.join(stakeholders_list)
        
        tags_to_set = [{
            'Key': 'Stakeholders',
            'Value': stakeholders_str
        }]
        
        response = _get_ec2_client().create_tags(
            Resources=[instance_id],
            Tags=tags_to_set
        )
        
        logger.info(f"Successfully set stakeholders tag for {instance_id}: {stakeholders_str}")
        _log_aws_operation("set_stakeholders_tag", instance_id, {
            "tags_set": [tag['Key'] for tag in tags_to_set],
            "stakeholders_count": len(stakeholders_list),
            "stakeholders": stakeholders_list
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error setting stakeholders tag for {instance_id}: {e}")
        _log_aws_operation("set_stakeholders_tag", instance_id, {
            "error": str(e),
            "stakeholders_count": len(stakeholders_list),
            "stakeholders": stakeholders_list
        }, False, e)
        return False

def delete_stakeholders_tag(instance_id):
    """Delete stakeholders tag for an EC2 instance"""
    try:
        response = _get_ec2_client().delete_tags(
            Resources=[instance_id],
            Tags=[
                {'Key': 'Stakeholders'}
            ]
        )
        
        logger.info(f"Successfully deleted stakeholders tag for {instance_id}")
        _log_aws_operation("delete_stakeholders_tag", instance_id, {
            "tags_deleted": ["Stakeholders"]
        })
        return True
        
    except Exception as e:
        logger.error(f"AWS Error deleting stakeholders tag for {instance_id}: {e}")
        _log_aws_operation("delete_stakeholders_tag", instance_id, {
            "error": str(e)
        }, False, e)
        return False

def add_stakeholder(instance_id, user_id):
    """Add a stakeholder to an EC2 instance"""
    try:
        # Get current stakeholders
        current_stakeholders_str = get_stakeholders_tag(instance_id)
        current_stakeholders = []
        
        if current_stakeholders_str:
            current_stakeholders = [s.strip() for s in current_stakeholders_str.split(',') if s.strip()]
        
        # Check if user is already a stakeholder
        if user_id in current_stakeholders:
            logger.info(f"User {user_id} is already a stakeholder for instance {instance_id}")
            _log_aws_operation("add_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "already_stakeholder",
                "current_stakeholders_count": len(current_stakeholders)
            })
            return True, "already_stakeholder"
        
        # Check if we're at the maximum limit
        if len(current_stakeholders) >= 10:
            logger.warning(f"Cannot add stakeholder {user_id} to instance {instance_id}: max limit reached")
            _log_aws_operation("add_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "max_limit_reached",
                "current_stakeholders_count": len(current_stakeholders)
            }, False)
            return False, "max_limit_reached"
        
        # Add new stakeholder
        new_stakeholders = current_stakeholders + [user_id]
        success = set_stakeholders_tag(instance_id, new_stakeholders)
        
        if success:
            logger.info(f"Successfully added stakeholder {user_id} to instance {instance_id}")
            _log_aws_operation("add_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "added",
                "previous_stakeholders_count": len(current_stakeholders),
                "new_stakeholders_count": len(new_stakeholders)
            })
            return True, "added"
        else:
            logger.error(f"Failed to add stakeholder {user_id} to instance {instance_id}")
            _log_aws_operation("add_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "failed",
                "current_stakeholders_count": len(current_stakeholders)
            }, False)
            return False, "failed"
            
    except Exception as e:
        logger.error(f"Error adding stakeholder {user_id} to instance {instance_id}: {e}")
        _log_aws_operation("add_stakeholder", instance_id, {
            "user_id": user_id,
            "action": "error",
            "error": str(e)
        }, False, e)
        return False, "error"

def remove_stakeholder(instance_id, user_id):
    """Remove a stakeholder from an EC2 instance"""
    try:
        # Get current stakeholders
        current_stakeholders_str = get_stakeholders_tag(instance_id)
        current_stakeholders = []
        
        if current_stakeholders_str:
            current_stakeholders = [s.strip() for s in current_stakeholders_str.split(',') if s.strip()]
        
        # Check if user is a stakeholder
        if user_id not in current_stakeholders:
            logger.info(f"User {user_id} is not a stakeholder for instance {instance_id}")
            _log_aws_operation("remove_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "not_stakeholder",
                "current_stakeholders_count": len(current_stakeholders)
            })
            return True, "not_stakeholder"
        
        # Remove stakeholder
        new_stakeholders = [s for s in current_stakeholders if s != user_id]
        
        # If no stakeholders remain, delete the tag entirely
        if not new_stakeholders:
            success = delete_stakeholders_tag(instance_id)
            action = "removed_and_deleted_tag"
        else:
            success = set_stakeholders_tag(instance_id, new_stakeholders)
            action = "removed"
        
        if success:
            logger.info(f"Successfully removed stakeholder {user_id} from instance {instance_id}")
            _log_aws_operation("remove_stakeholder", instance_id, {
                "user_id": user_id,
                "action": action,
                "previous_stakeholders_count": len(current_stakeholders),
                "new_stakeholders_count": len(new_stakeholders)
            })
            return True, action
        else:
            logger.error(f"Failed to remove stakeholder {user_id} from instance {instance_id}")
            _log_aws_operation("remove_stakeholder", instance_id, {
                "user_id": user_id,
                "action": "failed",
                "current_stakeholders_count": len(current_stakeholders)
            }, False)
            return False, "failed"
            
    except Exception as e:
        logger.error(f"Error removing stakeholder {user_id} from instance {instance_id}: {e}")
        _log_aws_operation("remove_stakeholder", instance_id, {
            "user_id": user_id,
            "action": "error",
            "error": str(e)
        }, False, e)
        return False, "error"

def get_instances_by_stakeholder(user_id):
    """Get all instances where a user is a stakeholder"""
    try:
        # Get all controllable instances
        instances = get_controllable_instances()
        user_instances = []
        
        for instance in instances:
            instance_id = instance['InstanceId']
            stakeholders_str = get_stakeholders_tag(instance_id)
            
            if stakeholders_str:
                stakeholders = [s.strip() for s in stakeholders_str.split(',') if s.strip()]
                if user_id in stakeholders:
                    instance_name = get_instance_name(instance_id)
                    user_instances.append({
                        'instance_id': instance_id,
                        'instance_name': instance_name,
                        'state': get_instance_state(instance_id)
                    })
        
        logger.info(f"Found {len(user_instances)} instances where user {user_id} is a stakeholder")
        _log_aws_operation("get_instances_by_stakeholder", user_id, {
            "instances_found": len(user_instances),
            "instance_ids": [inst['instance_id'] for inst in user_instances]
        })
        return user_instances
        
    except Exception as e:
        logger.error(f"Error getting instances for stakeholder {user_id}: {e}")
        _log_aws_operation("get_instances_by_stakeholder", user_id, {
            "error": str(e)
        }, False, e)
        return []

def is_user_stakeholder(instance_id, user_id):
    """Check if a user is a stakeholder for a specific instance"""
    try:
        # Get current stakeholders
        current_stakeholders_str = get_stakeholders_tag(instance_id)
        current_stakeholders = []
        
        if current_stakeholders_str:
            current_stakeholders = [s.strip() for s in current_stakeholders_str.split(',') if s.strip()]
        
        is_stakeholder = user_id in current_stakeholders
        
        logger.info(f"User {user_id} is {'a' if is_stakeholder else 'not a'} stakeholder for instance {instance_id}")
        _log_aws_operation("is_user_stakeholder", instance_id, {
            "user_id": user_id,
            "is_stakeholder": is_stakeholder,
            "current_stakeholders_count": len(current_stakeholders)
        })
        return is_stakeholder
        
    except Exception as e:
        logger.error(f"Error checking if user {user_id} is stakeholder for instance {instance_id}: {e}")
        _log_aws_operation("is_user_stakeholder", instance_id, {
            "user_id": user_id,
            "error": str(e)
        }, False, e)
        return False