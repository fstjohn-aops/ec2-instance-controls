#!/bin/bash

# EKS Deployment Script for EC2 Instance Controls
# This script builds and deploys the application to EKS

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME}
NAMESPACE="ec2-controls"
APP_NAME="ec2-instance-controls"

# Registry configuration - update these for your Nexus registry
REGISTRY_URL=${REGISTRY_URL:-"your-nexus-registry.com"}
REGISTRY_USERNAME=${REGISTRY_USERNAME}
REGISTRY_PASSWORD=${REGISTRY_PASSWORD}
IMAGE_NAME="${REGISTRY_URL}/ec2-instance-controls"
IMAGE_TAG=${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== EKS Deployment for EC2 Instance Controls ===${NC}"

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
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    # Check if we can connect to Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
        exit 1
    fi
    
    # Get AWS account ID if not set
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        if command -v aws &> /dev/null; then
            AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
        fi
        if [ -z "$AWS_ACCOUNT_ID" ]; then
            print_warning "AWS_ACCOUNT_ID not set. You'll need to update the manifests manually."
        else
            print_status "Using AWS Account ID: $AWS_ACCOUNT_ID"
        fi
    fi
    
    # Check registry credentials
    if [ -z "$REGISTRY_USERNAME" ] || [ -z "$REGISTRY_PASSWORD" ]; then
        print_warning "Registry credentials not set. You may need to login manually."
    fi
    
    print_status "All prerequisites met!"
}

# Login to registry
login_to_registry() {
    if [ -n "$REGISTRY_USERNAME" ] && [ -n "$REGISTRY_PASSWORD" ]; then
        print_status "Logging into registry..."
        echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY_URL" -u "$REGISTRY_USERNAME" --password-stdin
    else
        print_warning "Skipping registry login. Please ensure you're logged in manually."
    fi
}

# Build Docker image
build_image() {
    print_status "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
    
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:latest"
    
    print_status "Docker image built successfully!"
}

# Push image to registry
push_image() {
    print_status "Pushing image to registry..."
    
    docker push "${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${IMAGE_NAME}:latest"
    
    print_status "Image pushed successfully!"
}

# Update Kubernetes manifests
update_manifests() {
    print_status "Updating Kubernetes manifests..."
    
    # Update deployment with new image
    sed -i.bak "s|image: .*|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml
    
    # Update AWS account ID in manifests if available
    if [ -n "$AWS_ACCOUNT_ID" ]; then
        sed -i.bak "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" k8s/deployment.yaml
        sed -i.bak "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g" k8s/service-account.yaml
        print_status "Updated AWS Account ID in manifests"
    else
        print_warning "Please manually update AWS_ACCOUNT_ID in k8s/deployment.yaml and k8s/service-account.yaml"
    fi
    
    # Clean up backup files
    rm -f k8s/*.bak
    
    print_status "Manifests updated!"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests in order
    print_status "Applying service account..."
    kubectl apply -f k8s/service-account.yaml -n "$NAMESPACE"
    
    print_status "Applying configmap..."
    kubectl apply -f k8s/configmap.yaml -n "$NAMESPACE"
    
    print_status "Applying secrets..."
    kubectl apply -f k8s/secrets.yaml -n "$NAMESPACE"
    
    print_status "Applying persistent volume..."
    kubectl apply -f k8s/persistent-volume.yaml -n "$NAMESPACE"
    
    print_status "Applying persistent volume claim..."
    kubectl apply -f k8s/ebs-storage.yaml -n "$NAMESPACE"
    
    print_status "Applying deployment..."
    kubectl apply -f k8s/deployment.yaml -n "$NAMESPACE"
    
    print_status "Applying service..."
    kubectl apply -f k8s/service.yaml -n "$NAMESPACE"
    
    print_status "Deployment completed!"
}

# Wait for deployment to be ready
wait_for_deployment() {
    print_status "Waiting for deployment to be ready..."
    
    kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout=300s
    
    if [ $? -eq 0 ]; then
        print_status "Deployment is ready!"
    else
        print_error "Deployment failed to become ready"
        exit 1
    fi
}

# Show deployment summary
show_summary() {
    print_status "Deployment Complete!"
    echo ""
    echo -e "${BLUE}=== Summary ===${NC}"
    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "Namespace: ${NAMESPACE}"
    echo "App Name: ${APP_NAME}"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "kubectl get pods -n ${NAMESPACE}"
    echo "kubectl logs -f deployment/${APP_NAME} -n ${NAMESPACE}"
    echo "kubectl port-forward service/${APP_NAME} 8000:8000 -n ${NAMESPACE}"
    echo ""
    echo -e "${GREEN}Application endpoints:${NC}"
    echo "Health check: kubectl port-forward service/${APP_NAME} 8000:8000 -n ${NAMESPACE} && curl http://localhost:8000/health"
}

# Main execution
main() {
    check_prerequisites
    login_to_registry
    build_image
    push_image
    update_manifests
    deploy_to_kubernetes
    wait_for_deployment
    show_summary
}

# Run main function
main 