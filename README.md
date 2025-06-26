# EC2 Instance Controls - Slack Bot

A Kubernetes-native Slack bot for managing EC2 instances through Slack commands. Designed to run on Amazon EKS with IAM roles for service accounts.

## Features

- **Slack Integration**: Control EC2 instances directly from Slack
- **EC2 Power Management**: Start, stop, and check status of EC2 instances
- **Instance Scheduling**: Schedule automatic start/stop of instances
- **User Access Control**: Role-based access to specific instances
- **Audit Logging**: Comprehensive logging of all operations
- **Kubernetes Native**: Designed for EKS with IAM roles for service accounts

## Architecture

- **Flask Application**: HTTP API server with Slack integration
- **AWS SDK**: EC2 operations using IAM roles
- **Persistent Storage**: Schedules stored in EBS volumes
- **IAM Authentication**: Uses EKS service accounts for AWS access
- **Slack Events API**: Handles Slack commands and interactions

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

### 2. Deploy Application

Deploy to EKS using the new Kubernetes configuration:

```bash
# Deploy everything
kubectl apply -f k8s/

# Or deploy individual components
kubectl apply -f k8s/00-namespace.yml
kubectl apply -f k8s/04-configmap.yml
kubectl apply -f k8s/01-deployment.yml
kubectl apply -f k8s/02-service.yml
kubectl apply -f k8s/03-ingress.yml
```

## Configuration

### Environment Variables

The application uses these environment variables (configured via ConfigMap):

- `AWS_REGION`: AWS region for EC2 operations
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `SCHEDULE_DIR`: Directory for storing schedules
- `PORT`: Application port (default: 8000)

## API Endpoints

- `GET /health` - Health check
- `POST /slack/events` - Slack Events API endpoint
- `POST /instances` - List user's instances
- `POST /admin/check` - Check admin status
- `POST /ec2/power` - Control instance power state
- `POST /ec2-schedule` - Manage instance schedules

## Slack Commands

### Check Instance Status
```
/ec2 status i-1234567890abcdef0
```

### Start Instance
```
/ec2 start i-1234567890abcdef0
```

### Stop Instance
```
/ec2 stop i-1234567890abcdef0
```

### List Instances
```
/ec2 list
```

## Updating the Application

### Update Image Version
```bash
# Update to a specific version
./k8s/update-deployment.sh v1.2.3

# Update to latest
./k8s/update-deployment.sh latest
```

### Full Redeployment
```bash
# Remove and reapply all resources
kubectl delete -f k8s/
kubectl apply -f k8s/
```

## Monitoring

### View Logs
```bash
kubectl logs -f deployment/ec2-slack-bot -n ec2-slack-bot
```

### Check Pod Status
```bash
kubectl get pods -n ec2-slack-bot
```

### Port Forward for Testing
```bash
kubectl port-forward service/ec2-slack-bot 8000:80 -n ec2-slack-bot
```

### Check Service Status
```bash
kubectl get svc -n ec2-slack-bot
kubectl get ingress -n ec2-slack-bot
```

## Kubernetes Resources

The deployment creates several Kubernetes resources:

- **Namespace**: `ec2-slack-bot` - Isolated namespace for the Slack bot
- **Deployment**: `ec2-slack-bot` - Main application deployment
- **Service**: `ec2-slack-bot` - Internal service for the deployment
- **Ingress**: `ec2-slack-bot` - External access with TLS and IP whitelist
- **ConfigMap**: `ec2-slack-bot-config` - Application configuration

## Security

- **IAM Roles**: Uses EKS service accounts for AWS authentication
- **No Hardcoded Credentials**: All AWS access through IAM roles
- **Audit Logging**: All operations logged with user context
- **Role-Based Access**: Users can only access authorized instances
- **IP Whitelist**: Ingress restricted to office IP addresses
- **TLS Encryption**: HTTPS with Let's Encrypt certificates

## Troubleshooting

### Common Issues

1. **IAM Role Not Working**: Ensure OIDC provider is configured and service account has correct annotations
2. **Image Pull Errors**: Check registry credentials and image path
3. **Pod Startup Failures**: Check logs for configuration issues

### Debug Commands

```bash
# Check service account
kubectl describe serviceaccount ec2-controls-sa -n ec2-slack-bot

# Check pod events
kubectl describe pod -l app=ec2-slack-bot -n ec2-slack-bot

# Check AWS credentials in pod
kubectl exec -it deployment/ec2-slack-bot -n ec2-slack-bot -- env | grep AWS

# Check ingress status
kubectl describe ingress ec2-slack-bot -n ec2-slack-bot
```

### Health Checks

```bash
# Test health endpoint
curl https://ec2-slack-bot.aops.ninja/health

# Check application logs
kubectl logs -f deployment/ec2-slack-bot -n ec2-slack-bot
```
