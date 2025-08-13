# EC2 Instance Controls - Slack Bot

A Kubernetes-native Slack bot for managing EC2 instances through Slack commands. Designed to run on Amazon EKS with IAM roles for service accounts (IRSA) and EKS Pod Identity.

## Features

- **Slack Integration**: Control EC2 instances directly from Slack using slash commands
- **EC2 Power Management**: Start, stop, and restart EC2 instances
- **Instance Scheduling**: Schedule automatic start/stop of instances using EC2 tags
- **Fuzzy Search**: Search instances by name or ID with intelligent matching
- **Comprehensive Auditing**: Structured JSON logging of all operations with user context
- **Security-First**: Uses EKS Pod Identity for AWS authentication, no hardcoded credentials
- **Instance Control Validation**: Only controls instances with `EC2ControlsEnabled` tag set to truthy value

## Architecture

- **Flask Application**: HTTP API server handling Slack Events API
- **AWS SDK (boto3)**: EC2 operations using IAM roles via EKS Pod Identity
- **Persistent Scheduling**: Schedules stored as EC2 tags (`PowerScheduleOnTime`, `PowerScheduleOffTime`)
- **Structured Logging**: JSON-formatted logs with audit trail for all operations
- **Containerized**: Docker container with non-root user and security hardening

## Prerequisites

- Amazon EKS cluster with EKS Pod Identity configured
- kubectl configured for your cluster
- Podman installed locally (for building images)
- Access to container registry (cr.aops.tools)
- Slack app configured with Events API

## Quick Start

### 1. Deploy to Kubernetes

```bash
# Deploy all Kubernetes resources
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n ec2-slack-bot
kubectl get svc -n ec2-slack-bot
kubectl get ingress -n ec2-slack-bot
```

### 2. Build and Update Application

```bash
# Build and push new image version
./push-image.sh v1.0.0

# Update deployment with new image
./k8s/update-deployment.sh v1.0.0
```

## API Endpoints

The application exposes the following endpoints for Slack integration:

- `GET /health` - Health check endpoint
- `POST /instances` - List all controllable instances in the AWS region
- `POST /search` - Fuzzy search for instances by name or ID
- `POST /ec2/power` - Control instance power state (start/stop/restart)
- `POST /ec2-power-state` - Alias for power control endpoint
- `POST /ec2-schedule` - Manage instance schedules
- `POST /ec2-pause-scheduler` - Temporarily pause the scheduler for an instance
- `POST /ec2-stakeholder` - Manage instance stakeholder status

## Slack Commands

### List Instances
```
/instances
```
Lists all EC2 instances that can be controlled by the bot (have `EC2ControlsEnabled` tag).

### Search Instances
```
/search <instance-name-or-id>
```
Performs fuzzy search for instances by name or ID. Supports partial matches and intelligent sorting.

### Power Control
```
/ec2-power <instance-id|instance-name> [on|off|restart]
```
- `i-1234567890abcdef0` - Check current state
- `i-1234567890abcdef0 on` - Start instance
- `i-1234567890abcdef0 off` - Stop instance
- `i-1234567890abcdef0 restart` - Restart instance
- `my-instance-name on` - Use instance name instead of ID

### Instance Scheduling
```
/ec2-schedule <instance-id|instance-name> [<start_time> to <stop_time>|clear]
```
- `i-1234567890abcdef0` - Check current schedule
- `i-1234567890abcdef0 9:00am to 5:00pm` - Set daily schedule
- `i-1234567890abcdef0 clear` - Remove schedule

**Time Format Support:**
- `9:00am`, `9am`, `09:00`, `9:00 AM`
- `5:00pm`, `5pm`, `17:00`, `5:00 PM`

### Pause Scheduler
```
/ec2-pause-scheduler <instance-id|instance-name> [<hours>|cancel]
```
- `i-1234567890abcdef0` - Check current pause status
- `i-1234567890abcdef0 2h` - Pause scheduler for 2 hours
- `i-1234567890abcdef0 24h` - Pause scheduler for 24 hours
- `i-1234567890abcdef0 cancel` - Resume scheduler immediately

**Hours Format Support:**
- `1h`, `2h`, `24h`, `48h`, etc.
- Minimum: 1 hour
- Maximum: No limit (use responsibly)

### Instance Stakeholder Management
```
/ec2-stakeholder <instance-id|instance-name> [claim|remove|check]
```
- `i-1234567890abcdef0` - Claim instance (default action)
- `i-1234567890abcdef0 claim` - Explicitly claim instance
- `i-1234567890abcdef0 remove` - Remove yourself as stakeholder
- `i-1234567890abcdef0 check` - Check if you are a stakeholder

**Features:**
- Users can claim instances as stakeholders (max 10 per instance)
- Users can remove themselves as stakeholders
- Users can check their stakeholder status on specific instances
- Only works with instances that have `EC2ControlsEnabled` tag

## Security Model

### Instance Control Authorization
Only instances with the `EC2ControlsEnabled` tag set to a truthy value can be controlled. This provides fine-grained control over which instances the bot can manage.

### AWS Authentication
- Uses EKS Pod Identity for AWS authentication
- No hardcoded credentials or access keys
- IAM permissions scoped to EC2 operations only
- Service account: `ec2-instance-controls` in namespace `ec2-slack-bot`

### Network Security
- Ingress configured with TLS encryption
- IP whitelist capability (currently commented out)
- Non-root container execution
- Security context hardening

## Configuration

### Environment Variables (ConfigMap)

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-west-2` | AWS region for EC2 operations |
| `LOG_LEVEL` | `INFO` | Application logging level |
| `PORT` | `8000` | Application port |
| `TEST_MODE` | `false` | Test mode flag |

### AWS IAM Permissions

The service requires the following IAM permissions:
- `ec2:*` - Full EC2 access for instance management
- `kms:*` - KMS access for encrypted resources
- `iam:PassRole` - For passing IAM roles to EC2 instances

## Deployment

### Kubernetes Resources

The deployment creates:

- **Namespace**: `ec2-slack-bot` - Isolated namespace
- **ServiceAccount**: `ec2-instance-controls` - For AWS authentication
- **Deployment**: `ec2-slack-bot` - Main application with 1 replica
- **Service**: `ec2-slack-bot` - Internal service (port 80)
- **Ingress**: `ec2-slack-bot` - External access with TLS
- **ConfigMap**: `ec2-slack-bot-config` - Application configuration

### Container Image

- **Registry**: `cr.aops.tools/aops-docker-repo/ec2-instance-controls`
- **Base Image**: `python:3.11-slim`
- **Web Server**: Gunicorn with 1 worker
- **Health Check**: HTTP GET `/health` endpoint

### Build and Deploy Workflow

```bash
# 1. Build image for x86_64 (EKS compatibility)
./build-image.sh v1.0.0

# 2. Build and push to registry
./push-image.sh v1.0.0

# 3. Update deployment
./k8s/update-deployment.sh v1.0.0
```

## Monitoring and Logging

### Structured Logging
All operations are logged in JSON format with audit information:
- User actions (AUDIT)
- AWS operations (AWS_AUDIT)
- Schedule operations (SCHEDULE_AUDIT)
- Request tracking (REQUEST_AUDIT)

### Health Monitoring
```bash
# Check application health
curl https://ec2-slack-bot.notaops.com/health

# View application logs
kubectl logs -f deployment/ec2-slack-bot -n ec2-slack-bot

# Check pod status
kubectl get pods -n ec2-slack-bot

# Monitor deployment
kubectl rollout status deployment/ec2-slack-bot -n ec2-slack-bot
```

### Port Forward for Local Testing
```bash
kubectl port-forward service/ec2-slack-bot 8000:80 -n ec2-slack-bot
```

## Development

### Local Development Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
./test.sh

# Run application locally
python app.py
```

### Testing
The project includes comprehensive tests:
- Unit tests for all endpoints
- Mocked AWS operations
- Integration tests for handlers

Run tests with:
```bash
./test.sh
```

### Dependencies
- **Flask 3.0.0** - Web framework
- **boto3 1.34.0** - AWS SDK
- **python-dateutil 2.8.2** - Date/time parsing
- **gunicorn 21.2.0** - WSGI server
- **pytest 7.4.3** - Testing framework

## Troubleshooting

### Common Issues

1. **Instance Not Found**
   - Verify instance exists in the configured AWS region
   - Check that instance has `EC2ControlsEnabled` tag set to truthy value

2. **Permission Denied**
   - Verify EKS Pod Identity is configured correctly
   - Check service account has proper IAM role association
   - Ensure IAM role has required EC2 permissions

3. **Image Pull Errors**
   - Verify registry credentials are configured
   - Check image tag exists in registry
   - Ensure cluster can access the container registry

### Debug Commands

```bash
# Check pod events
kubectl describe pod -l app=ec2-slack-bot -n ec2-slack-bot

# Verify AWS credentials in pod
kubectl exec -it deployment/ec2-slack-bot -n ec2-slack-bot -- env | grep AWS

# Check ingress status
kubectl describe ingress ec2-slack-bot -n ec2-slack-bot

# View recent logs
kubectl logs --tail=100 deployment/ec2-slack-bot -n ec2-slack-bot
```

### Health Checks

```bash
# Test health endpoint
curl https://ec2-slack-bot.notaops.com/health

# Check application logs
kubectl logs -f deployment/ec2-slack-bot -n ec2-slack-bot

# Verify service endpoints
kubectl get endpoints -n ec2-slack-bot
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is proprietary and confidential.

## Planned Features

- allow users to set schedules for specific days and then an abstraction layer
for like weekends and weekdays
- add handling for rebooting an OFF instance
