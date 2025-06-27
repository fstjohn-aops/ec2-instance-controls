# EC2 Instance Controls - Slack Bot

A Kubernetes-native Slack bot for managing EC2 instances through Slack commands. Designed to run on Amazon EKS with IAM roles for service accounts.

## Features

- **Slack Integration**: Control EC2 instances directly from Slack
- **EC2 Power Management**: Start, stop, and check status of EC2 instances
- **Instance Scheduling**: Schedule automatic start/stop of instances
- **Audit Logging**: Comprehensive logging of all operations
- **Kubernetes Native**: Designed for EKS with IAM roles for service accounts

## Architecture

- **Flask Application**: HTTP API server with Slack integration
- **AWS SDK**: EC2 operations using IAM roles
- **Persistent Storage**: Schedules stored in EBS volumes
- **IAM Authentication**: Uses EKS service accounts for AWS access
- **Slack Events API**: Handles Slack commands and interactions

## Prerequisites

- Amazon EKS cluster with IAM roles configured
- kubectl configured for your cluster
- Podman installed locally (for building images)
- Access to container registry (cr.aops.tools)

## Quick Start

### 1. Build and Deploy

Build the container image and deploy to your cluster:

```bash
# Build and push image to registry
./push-image.sh v1.0.0

# Deploy to Kubernetes
kubectl apply -f k8s/

# Update deployment with new image
./k8s/update-deployment.sh v1.0.0
```

### 2. Alternative: Deploy Individual Components

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

## Build and Deployment

### Building Images

The project includes scripts for building and deploying container images:

```bash
# Build image for x86_64 (EKS compatibility)
./build-image.sh v1.0.0

# Build and push to registry
./push-image.sh v1.0.0
```

### Container Registry

Images are built and pushed to: `cr.aops.tools/aops-docker-repo/ec2-instance-controls`

### Deployment Workflow

1. **Build**: `./build-image.sh <tag>` - Builds x86_64 image locally
2. **Push**: `./push-image.sh <tag>` - Builds and pushes to registry
3. **Deploy**: `./k8s/update-deployment.sh <tag>` - Updates Kubernetes deployment

## Configuration

### Environment Variables

The application uses these environment variables (configured via ConfigMap):

- `AWS_REGION`: AWS region for EC2 operations
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `PORT`: Application port (default: 8000)

## API Endpoints

- `GET /health` - Health check
- `POST /slack/events` - Slack Events API endpoint
- `POST /instances` - List all instances in the AWS region
- `POST /search` - Fuzzy search for instances by name or ID
- `POST /ec2/power` - Control instance power state
- `POST /ec2-schedule` - Manage instance schedules

## Updating the Application

### Update Image Version
```bash
# Build and push new version
./push-image.sh v1.2.3

# Update deployment
./k8s/update-deployment.sh v1.2.3
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
- **IP Whitelist**: Ingress restricted to office IP addresses
- **TLS Encryption**: HTTPS with Let's Encrypt certificates

## Troubleshooting

### Common Issues

1. **IAM Role Not Working**: Ensure OIDC provider is configured and service account has correct annotations
2. **Image Pull Errors**: Check registry credentials and image path
3. **Pod Startup Failures**: Check logs for configuration issues

### Debug Commands

```bash
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
