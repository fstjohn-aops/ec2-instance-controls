# Auditing and Logging System

Since we removed Role-Based Access Control (RBAC) and now allow any authenticated Slack user to manage all EC2 instances, we've implemented a comprehensive auditing and logging system to track all user actions.

## Overview

The application now logs all user actions, AWS operations, and system events in a structured JSON format for easy parsing and analysis. This provides complete visibility into who is doing what with the EC2 instances.

## Log Categories

### 1. Request Auditing (`REQUEST_AUDIT`)
Logs all incoming HTTP requests with user identification and request details.

**Fields:**
- `timestamp`: ISO timestamp
- `method`: HTTP method (GET/POST)
- `endpoint`: Flask endpoint called
- `user_id`: Slack user ID
- `user_name`: Slack user name
- `remote_addr`: Client IP address
- `user_agent`: Client user agent
- `form_data`: Request form data (truncated for security)

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "method": "POST",
  "endpoint": "set_ec2_power",
  "user_id": "U08QYU6AX0V",
  "user_name": "John Doe",
  "remote_addr": "192.168.1.100",
  "user_agent": "Slackbot 1.0",
  "form_data": {
    "user_id": "U08QYU6AX0V",
    "text": "i-1234567890abcdef0 on"
  }
}
```

### 2. User Action Auditing (`AUDIT`)
Logs all user actions performed through the application.

**Fields:**
- `timestamp`: ISO timestamp
- `user_id`: Slack user ID
- `user_name`: Slack user name
- `action`: Action performed (e.g., `ec2_power_status`, `ec2_power_change`, `list_instances`)
- `target`: Target of the action (instance ID, "all", etc.)
- `details`: Action-specific details
- `status`: SUCCESS or FAILED

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "user_id": "U08QYU6AX0V",
  "user_name": "John Doe",
  "action": "ec2_power_change",
  "target": "i-1234567890abcdef0",
  "details": {
    "instance_name": "web-server-1",
    "power_state": "on",
    "original_identifier": "web-server-1"
  },
  "status": "SUCCESS"
}
```

### 3. AWS Operation Auditing (`AWS_AUDIT`)
Logs all AWS API calls and their results.

**Fields:**
- `timestamp`: ISO timestamp
- `aws_operation`: AWS operation name (e.g., `start_instances`, `describe_instances`)
- `target`: Target instance ID or operation target
- `region`: AWS region
- `details`: Operation-specific details
- `status`: SUCCESS or FAILED
- `error`: Error details if failed

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "aws_operation": "start_instances",
  "target": "i-1234567890abcdef0",
  "region": "us-west-2",
  "details": {
    "previous_state": "stopped",
    "current_state": "pending"
  },
  "status": "SUCCESS"
}
```

### 4. Schedule Operation Auditing (`SCHEDULE_AUDIT`)
Logs all schedule-related operations.

**Fields:**
- `timestamp`: ISO timestamp
- `schedule_operation`: Operation type (e.g., `set_schedule`, `delete_schedule`, `get_schedule`)
- `instance_id`: Target instance ID
- `details`: Operation-specific details
- `status`: SUCCESS or FAILED

**Example:**
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "schedule_operation": "set_schedule",
  "instance_id": "i-1234567890abcdef0",
  "details": {
    "start_time": "09:00",
    "stop_time": "17:00",
    "previous_schedule": null
  },
  "status": "SUCCESS"
}
```

## Log Analysis

### Common Queries

**Find all actions by a specific user:**
```bash
grep "user_id.*U08QYU6AX0V" app.log
```

**Find all power state changes:**
```bash
grep "action.*ec2_power" app.log
```

**Find failed operations:**
```bash
grep "status.*FAILED" app.log
```

**Find all AWS operations:**
```bash
grep "AWS_AUDIT" app.log
```

### Security Monitoring

The logs can be used to:

1. **Track user activity**: See who is accessing which instances
2. **Monitor power state changes**: Track when instances are started/stopped
3. **Audit schedule changes**: Monitor when schedules are modified
4. **Detect anomalies**: Identify unusual patterns or failed operations
5. **Compliance reporting**: Generate reports for security audits

### Log Retention

Consider implementing log rotation and retention policies:

```bash
# Example logrotate configuration
/app.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

## Integration with Monitoring Systems

The structured JSON logs can be easily integrated with:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **CloudWatch Logs** (if running on AWS)
- **Custom monitoring dashboards**

## Privacy and Security

- User IDs and names are logged for accountability
- Form data is truncated to prevent logging sensitive information
- All timestamps are in UTC for consistency
- Logs should be stored securely and access-controlled

## Compliance

This auditing system helps meet compliance requirements by providing:

- **Complete audit trail** of all user actions
- **User identification** for accountability
- **Action tracking** with timestamps
- **Success/failure logging** for troubleshooting
- **Structured format** for automated analysis 