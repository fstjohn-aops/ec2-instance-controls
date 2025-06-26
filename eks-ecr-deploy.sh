#!/bin/bash

# EKS + ECR Deployment Script for EC2 Instance Controls
# This script builds and deploys to EKS using ECR

set -e

# Configuration
IMAGE_NAME="ec2-instance-controls"
VERSION=${1:-latest}
AWS_REGION=${AWS_REGION:-us-west-2}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== EKS + ECR Deployment for EC2 Instance Controls ===${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Get AWS account ID if not set
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        print_status "Using AWS Account ID: $AWS_ACCOUNT_ID"
    fi
    
    # Check if EKS cluster name is provided
    if [ -z "$EKS_CLUSTER_NAME" ]; then
        print_error "EKS_CLUSTER_NAME environment variable not set"
        print_warning "Please set: export EKS_CLUSTER_NAME=your-cluster-name"
        exit 1
    fi
    
    print_status "All prerequisites met!"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t ${IMAGE_NAME}:${VERSION} .
    
    if [ $? -eq 0 ]; then
        print_status "Docker image built successfully: ${IMAGE_NAME}:${VERSION}"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Setup ECR repository
setup_ecr() {
    print_status "Setting up ECR repository..."
    
    # Login to ECR
    print_status "Logging in to Amazon ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Create repository if it doesn't exist
    print_status "Creating ECR repository if it doesn't exist..."
    aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} || \
    aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${AWS_REGION}
    
    # Set the full image name
    ECR_IMAGE_NAME="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${VERSION}"
    
    # Tag and push the image
    print_status "Tagging image for ECR..."
    docker tag ${IMAGE_NAME}:${VERSION} ${ECR_IMAGE_NAME}
    
    print_status "Pushing to Amazon ECR..."
    docker push ${ECR_IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        print_status "Successfully pushed to ECR: ${ECR_IMAGE_NAME}"
    else
        print_error "Failed to push to ECR"
        exit 1
    fi
}

# Update Kubernetes manifests
update_manifests() {
    print_status "Updating Kubernetes manifests..."
    
    # Update deployment.yaml with ECR image
    sed -i.bak "s|image: ec2-instance-controls:latest|image: ${ECR_IMAGE_NAME}|g" k8s/deployment.yaml
    
    # Update configmap with AWS region
    sed -i.bak "s|AWS_REGION: \"us-west-2\"|AWS_REGION: \"${AWS_REGION}\"|g" k8s/configmap.yaml
    
    print_status "Kubernetes manifests updated!"
}

# Deploy to EKS
deploy_to_eks() {
    print_status "Deploying to EKS cluster: ${EKS_CLUSTER_NAME}"
    
    # Update kubeconfig
    print_status "Updating kubeconfig..."
    aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}
    
    # Create namespace if it doesn't exist
    print_status "Creating namespace..."
    kubectl create namespace ec2-controls --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    print_status "Applying Kubernetes manifests..."
    kubectl apply -f k8s/ -n ec2-controls
    
    # Wait for deployment to be ready
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ec2-instance-controls -n ec2-controls
    
    if [ $? -eq 0 ]; then
        print_status "Deployment successful!"
    else
        print_error "Deployment failed or timed out"
        exit 1
    fi
}

# Show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    
    # Show pods
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods -n ec2-controls -l app=ec2-instance-controls
    
    echo ""
    
    # Show services
    echo -e "${BLUE}Services:${NC}"
    kubectl get svc -n ec2-controls
    
    echo ""
    
    # Show logs
    echo -e "${BLUE}Recent logs:${NC}"
    kubectl logs -n ec2-controls -l app=ec2-instance-controls --tail=10
    
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo "Image: ${ECR_IMAGE_NAME}"
    echo "Cluster: ${EKS_CLUSTER_NAME}"
    echo "Namespace: ec2-controls"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "kubectl logs -f -n ec2-controls -l app=ec2-instance-controls"
    echo "kubectl port-forward -n ec2-controls svc/ec2-instance-controls 8000:80"
    echo "kubectl delete -f k8s/ -n ec2-controls"
}

# Main execution
main() {
    check_prerequisites
    build_image
    setup_ecr
    update_manifests
    deploy_to_eks
    show_status
}

# Run main function
main 