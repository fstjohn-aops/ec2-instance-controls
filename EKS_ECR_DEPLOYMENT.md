# EKS + ECR Deployment Guide

This guide walks you through deploying the EC2 Instance Controls application to Amazon EKS using ECR for container images.

## Prerequisites

### **1. Required Tools**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install eksctl (optional, for OIDC setup)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

### **2. AWS Configuration**
```bash
# Configure AWS credentials
aws configure

# Set environment variables
export AWS_REGION=us-west-2
export EKS_CLUSTER_NAME=your-cluster-name
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

### **3. EKS Cluster**
Ensure you have an EKS cluster running:
```bash
# Check if cluster exists
aws eks describe-cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION}

# If not, create one (example)
eksctl create cluster \
  --name ${EKS_CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4
```

## Quick Deployment

### **Option 1: Automated Script (Recommended)**
```bash
# 1. Set environment variables
export EKS_CLUSTER_NAME=your-cluster-name
export AWS_REGION=us-west-2

# 2. Setup IAM (one-time setup)
./aws/setup-iam.sh

# 3. Deploy application
./eks-ecr-deploy.sh v1.0.0
```

### **Option 2: Manual Steps**
```bash
# 1. Build and push to ECR
./build-and-deploy.sh v1.0.0 ecr

# 2. Apply Kubernetes manifests
kubectl apply -f k8s/ -n ec2-controls
```

## Detailed Steps

### **Step 1: Setup IAM Role and Policy**

The application needs AWS permissions to manage EC2 instances. We use IAM Roles for Service Accounts (IRSA) for secure access.

```bash
# Run the IAM setup script
./aws/setup-iam.sh
```

This creates:
- **IAM Policy**: `EC2ControlsPolicy` with EC2 and ECR permissions
- **IAM Role**: `ec2-controls-role` with trust relationship to EKS
- **OIDC Provider**: Links EKS cluster to IAM

### **Step 2: Build and Push Container Image**

```bash
# Build and push to ECR
./eks-ecr-deploy.sh v1.0.0
```

This script:
1. Builds the Docker image
2. Creates ECR repository (if needed)
3. Pushes image to ECR
4. Updates Kubernetes manifests
5. Deploys to EKS

### **Step 3: Verify Deployment**

```bash
# Check deployment status
kubectl get pods -n ec2-controls
kubectl get svc -n ec2-controls

# Check logs
kubectl logs -n ec2-controls -l app=ec2-instance-controls

# Check service account
kubectl get serviceaccount -n ec2-controls
```

## Architecture

### **EKS + ECR Integration**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ECR Registry  │    │   EKS Cluster   │    │   Application   │
│                 │    │                 │    │                 │
│ • Container     │───▶│ • Pods          │───▶│ • Flask App     │
│   Images        │    │ • Service       │    │ • EC2 Control   │
│ • Authentication│    │   Account       │    │ • Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   IAM Role      │
                       │                 │
                       │ • EC2 Permissions│
                       │ • ECR Access    │
                       └─────────────────┘
```

### **Security Model**
- **IAM Roles for Service Accounts**: Pods assume IAM roles via OIDC
- **Least Privilege**: Minimal permissions for EC2 operations
- **No Hardcoded Credentials**: Uses AWS SDK credential chain
- **Network Security**: Pods run in private subnets

## Configuration

### **Environment Variables**
```yaml
# From ConfigMap
AWS_REGION: "us-west-2"
LOG_LEVEL: "INFO"
SCHEDULE_DIR: "/app/schedules"

# From Secrets (optional with IAM role)
AWS_ACCESS_KEY_ID: (optional)
AWS_SECRET_ACCESS_KEY: (optional)
SLACK_BOT_TOKEN: (required)
SLACK_SIGNING_SECRET: (required)
```

### **Storage**
- **EBS Volume**: Persistent storage for schedules
- **Storage Class**: `gp3` for cost-effective performance
- **Size**: 1GB (configurable)

### **Resources**
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

## Monitoring and Logging

### **CloudWatch Integration**
```bash
# View logs in CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/eks/${EKS_CLUSTER_NAME}"

# Stream logs
aws logs tail /aws/eks/${EKS_CLUSTER_NAME}/application --follow
```

### **Kubernetes Logs**
```bash
# View application logs
kubectl logs -n ec2-controls -l app=ec2-instance-controls

# Follow logs in real-time
kubectl logs -f -n ec2-controls -l app=ec2-instance-controls

# View logs from specific pod
kubectl logs -n ec2-controls ec2-instance-controls-abc123
```

### **Metrics and Health Checks**
```bash
# Check pod health
kubectl get pods -n ec2-controls -o wide

# Check service endpoints
kubectl get endpoints -n ec2-controls

# Test health endpoint
kubectl port-forward -n ec2-controls svc/ec2-instance-controls 8000:80
curl http://localhost:8000/health
```

## Troubleshooting

### **Common Issues**

#### **1. Image Pull Errors**
```bash
# Check if image exists in ECR
aws ecr describe-images --repository-name ec2-instance-controls --region ${AWS_REGION}

# Check pod events
kubectl describe pod -n ec2-controls <pod-name>
```

#### **2. IAM Permission Issues**
```bash
# Check if service account can assume role
kubectl get serviceaccount -n ec2-controls ec2-controls-sa -o yaml

# Check pod annotations
kubectl get pod -n ec2-controls <pod-name> -o yaml | grep -A 5 annotations
```

#### **3. Storage Issues**
```bash
# Check PVC status
kubectl get pvc -n ec2-controls

# Check PV status
kubectl get pv

# Check storage class
kubectl get storageclass
```

### **Debug Commands**
```bash
# Get detailed pod information
kubectl describe pod -n ec2-controls <pod-name>

# Check pod logs
kubectl logs -n ec2-controls <pod-name>

# Execute into pod
kubectl exec -it -n ec2-controls <pod-name> -- /bin/bash

# Check AWS credentials in pod
kubectl exec -n ec2-controls <pod-name> -- aws sts get-caller-identity
```

## Scaling and Updates

### **Scaling**
```bash
# Scale deployment
kubectl scale deployment ec2-instance-controls -n ec2-controls --replicas=3

# Auto-scaling (if HPA is configured)
kubectl autoscale deployment ec2-instance-controls -n ec2-controls --cpu-percent=70 --min=2 --max=5
```

### **Updates**
```bash
# Update to new version
./eks-ecr-deploy.sh v1.1.0

# Rollback if needed
kubectl rollout undo deployment ec2-instance-controls -n ec2-controls

# Check rollout status
kubectl rollout status deployment ec2-instance-controls -n ec2-controls
```

## Cost Optimization

### **Resource Optimization**
- **CPU/Memory**: Start with small requests, monitor usage
- **Storage**: Use gp3 for better cost/performance
- **Nodes**: Use Spot instances for non-critical workloads

### **Monitoring Costs**
```bash
# Check ECR costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Check EKS costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Container Service for Kubernetes"]}}'
```

## Security Best Practices

### **Network Security**
- Use private subnets for pods
- Configure security groups appropriately
- Use Network Policies for pod-to-pod communication

### **IAM Security**
- Use least privilege principle
- Regularly audit IAM permissions
- Use AWS Config for compliance monitoring

### **Container Security**
- Scan images for vulnerabilities
- Use non-root user in containers
- Keep base images updated

## Cleanup

### **Remove Application**
```bash
# Delete application
kubectl delete -f k8s/ -n ec2-controls

# Delete namespace
kubectl delete namespace ec2-controls
```

### **Remove IAM Resources**
```bash
# Detach policy from role
aws iam detach-role-policy --role-name ec2-controls-role --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EC2ControlsPolicy

# Delete role
aws iam delete-role --role-name ec2-controls-role

# Delete policy
aws iam delete-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EC2ControlsPolicy
```

### **Remove ECR Repository**
```bash
# Delete all images
aws ecr batch-delete-image --repository-name ec2-instance-controls --image-ids imageTag=latest imageTag=v1.0.0

# Delete repository
aws ecr delete-repository --repository-name ec2-instance-controls
``` 