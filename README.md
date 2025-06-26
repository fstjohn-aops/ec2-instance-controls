# EC2 Instance Controls

A Kubernetes-native application for managing EC2 instances through HTTP APIs. Designed to run on Amazon EKS with IAM roles for service accounts.

## Features

- **EC2 Power Management**: Start, stop, and check status of EC2 instances
- **Instance Scheduling**: Schedule automatic start/stop of instances
- **User Access Control**: Role-based access to specific instances
- **Audit Logging**: Comprehensive logging of all operations
- **Kubernetes Native**: Designed for EKS with IAM roles for service accounts

## Architecture

- **Flask Application**: HTTP API server
- **AWS SDK**: EC2 operations using IAM roles
- **Persistent Storage**: Schedules stored in EBS volumes
- **IAM Authentication**: Uses EKS service accounts for AWS access

## Prerequisites

- Amazon EKS cluster
- kubectl configured for your cluster
- Docker installed locally
- Access to container registry (Nexus, ECR, etc.)

## Quick Start

### 1. Setup IAM Role

Create the necessary IAM resources for EKS service account authentication:

```bash
export EKS_CLUSTER_NAME="your-cluster-name"
export AWS_REGION="us-west-2"
./aws/setup-iam.sh
```

### 2. Configure Registry

Set your container registry details:

```bash
export REGISTRY_URL="your-nexus-registry.com"
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-password"
```

### 3. Deploy Application

Build and deploy to EKS:

```bash
./deploy.sh
```

## Configuration

### Environment Variables

The application uses these environment variables (configured via ConfigMap):

- `AWS_REGION`: AWS region for EC2 operations
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `SCHEDULE_DIR`: Directory for storing schedules

### Secrets

Optional Slack integration (if needed):
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_SIGNING_SECRET`: Slack signing secret

## API Endpoints

- `POST /health` - Health check
- `POST /instances` - List user's instances
- `POST /admin/check` - Check admin status
- `POST /ec2/power` - Control instance power state
- `POST /ec2-schedule` - Manage instance schedules

## Usage Examples

### Check Instance Status
```bash
curl -X POST http://localhost:8000/ec2/power \
  -d "user_id=U123456&user_name=john&text=i-1234567890abcdef0"
```

### Start Instance
```bash
curl -X POST http://localhost:8000/ec2/power \
  -d "user_id=U123456&user_name=john&text=i-1234567890abcdef0 on"
```

### List Instances
```bash
curl -X POST http://localhost:8000/instances \
  -d "user_id=U123456&user_name=john"
```

## Development

### Local Testing

For local development, you can run the application directly:

```bash
pip install -r requirements.txt
python app.py
```

### Building New Image

To update the application:

```bash
export IMAGE_TAG="v1.1"
./deploy.sh
```

## Monitoring

### View Logs
```bash
kubectl logs -f deployment/ec2-instance-controls -n ec2-controls
```

### Check Pod Status
```bash
kubectl get pods -n ec2-controls
```

### Port Forward for Testing
```bash
kubectl port-forward service/ec2-instance-controls 8000:8000 -n ec2-controls
```

## Security

- **IAM Roles**: Uses EKS service accounts for AWS authentication
- **No Hardcoded Credentials**: All AWS access through IAM roles
- **Audit Logging**: All operations logged with user context
- **Role-Based Access**: Users can only access authorized instances

## Troubleshooting

### Common Issues

1. **IAM Role Not Working**: Ensure OIDC provider is configured and service account has correct annotations
2. **Image Pull Errors**: Check registry credentials and image path
3. **Pod Startup Failures**: Check logs for configuration issues

### Debug Commands

```bash
# Check service account
kubectl describe serviceaccount ec2-controls-sa -n ec2-controls

# Check pod events
kubectl describe pod -l app=ec2-instance-controls -n ec2-controls

# Check AWS credentials in pod
kubectl exec -it deployment/ec2-instance-controls -n ec2-controls -- env | grep AWS
```

## License

[Add your license here]
