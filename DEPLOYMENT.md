# EKS Deployment Guide

This guide covers deploying the EC2 Instance Controls application to Amazon EKS.

## Prerequisites

- EKS cluster with OIDC provider configured
- kubectl configured for your cluster
- Docker installed locally
- Access to container registry (Nexus, ECR, etc.)

## Deployment Steps

### 1. Setup IAM Resources

Create the IAM role and policy for EKS service account authentication:

```bash
export EKS_CLUSTER_NAME="your-cluster-name"
export AWS_REGION="us-west-2"
./aws/setup-iam.sh
```

This creates:
- IAM policy with EC2 permissions
- IAM role with trust policy for your EKS cluster
- OIDC provider association (if needed)

### 2. Configure Container Registry

Set your registry details:

```bash
export REGISTRY_URL="your-nexus-registry.com"
export REGISTRY_USERNAME="your-username"
export REGISTRY_PASSWORD="your-password"
```

### 3. Deploy Application

Build and deploy:

```bash
./deploy.sh
```

This script:
- Builds Docker image
- Pushes to registry
- Updates Kubernetes manifests
- Deploys to EKS

## Configuration

### Environment Variables

Configure via `k8s/configmap.yaml`:
- `AWS_REGION`: AWS region for EC2 operations
- `LOG_LEVEL`: Logging level
- `SCHEDULE_DIR`: Directory for schedules

### Secrets

Optional Slack integration in `k8s/secrets.yaml`:
- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_SIGNING_SECRET`: Slack signing secret

## Updating the Application

To deploy a new version:

```bash
export IMAGE_TAG="v1.1"
./deploy.sh
```

Or update just the image:

```bash
kubectl set image deployment/ec2-instance-controls ec2-control-app=your-registry/ec2-instance-controls:v1.1 -n ec2-controls
```

## Monitoring

### Check Deployment Status

```bash
kubectl get pods -n ec2-controls
kubectl get services -n ec2-controls
```

### View Logs

```bash
kubectl logs -f deployment/ec2-instance-controls -n ec2-controls
```

### Test Application

```bash
# Port forward to access locally
kubectl port-forward service/ec2-instance-controls 8000:8000 -n ec2-controls

# Test health endpoint
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **IAM Role Not Working**
   - Check OIDC provider is configured
   - Verify service account has correct annotations
   - Check IAM role trust policy

2. **Image Pull Errors**
   - Verify registry credentials
   - Check image path in deployment
   - Ensure registry is accessible from cluster

3. **Pod Startup Failures**
   - Check pod events: `kubectl describe pod -n ec2-controls`
   - Check logs: `kubectl logs -n ec2-controls`
   - Verify ConfigMap and Secrets exist

### Debug Commands

```bash
# Check service account
kubectl describe serviceaccount ec2-controls-sa -n ec2-controls

# Check AWS credentials in pod
kubectl exec -it deployment/ec2-instance-controls -n ec2-controls -- env | grep AWS

# Check IAM role annotation
kubectl get pod -n ec2-controls -o yaml | grep -A 5 -B 5 eks.amazonaws.com/role-arn
```

## Cleanup

To remove the application:

```bash
kubectl delete namespace ec2-controls
```

To remove IAM resources:

```bash
aws iam detach-role-policy --role-name ec2-controls-role --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EC2ControlsPolicy
aws iam delete-role --role-name ec2-controls-role
aws iam delete-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EC2ControlsPolicy
``` 