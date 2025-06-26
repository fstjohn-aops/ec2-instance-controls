#!/bin/bash

# EC2 Instance Controls - Build and Deploy Script
# This script builds the Docker image and provides options for different registries

set -e

# Configuration
IMAGE_NAME="ec2-instance-controls"
VERSION=${1:-latest}
REGISTRY=${2:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== EC2 Instance Controls - Build and Deploy ===${NC}"

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
print_status "Building Docker image..."
docker build -t ${IMAGE_NAME}:${VERSION} .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully: ${IMAGE_NAME}:${VERSION}"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Function to push to different registries
push_to_registry() {
    local registry=$1
    local full_image_name=""
    
    case $registry in
        "dockerhub")
            if [ -z "$DOCKERHUB_USERNAME" ]; then
                print_error "DOCKERHUB_USERNAME environment variable not set"
                print_warning "Please set: export DOCKERHUB_USERNAME=your-username"
                return 1
            fi
            full_image_name="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
            docker tag ${IMAGE_NAME}:${VERSION} ${full_image_name}
            print_status "Pushing to Docker Hub..."
            docker push ${full_image_name}
            ;;
            
        "ecr")
            if [ -z "$AWS_REGION" ] || [ -z "$AWS_ACCOUNT_ID" ]; then
                print_error "AWS_REGION and AWS_ACCOUNT_ID environment variables not set"
                print_warning "Please set: export AWS_REGION=us-west-2"
                print_warning "Please set: export AWS_ACCOUNT_ID=your-account-id"
                return 1
            fi
            full_image_name="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${VERSION}"
            
            # Login to ECR
            print_status "Logging in to Amazon ECR..."
            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
            
            # Create repository if it doesn't exist
            print_status "Creating ECR repository if it doesn't exist..."
            aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} || \
            aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${AWS_REGION}
            
            docker tag ${IMAGE_NAME}:${VERSION} ${full_image_name}
            print_status "Pushing to Amazon ECR..."
            docker push ${full_image_name}
            ;;
            
        "gcr")
            if [ -z "$GCP_PROJECT_ID" ]; then
                print_error "GCP_PROJECT_ID environment variable not set"
                print_warning "Please set: export GCP_PROJECT_ID=your-project-id"
                return 1
            fi
            full_image_name="gcr.io/${GCP_PROJECT_ID}/${IMAGE_NAME}:${VERSION}"
            
            # Login to GCR
            print_status "Logging in to Google Container Registry..."
            gcloud auth configure-docker
            
            docker tag ${IMAGE_NAME}:${VERSION} ${full_image_name}
            print_status "Pushing to Google Container Registry..."
            docker push ${full_image_name}
            ;;
            
        "acr")
            if [ -z "$AZURE_REGISTRY_NAME" ]; then
                print_error "AZURE_REGISTRY_NAME environment variable not set"
                print_warning "Please set: export AZURE_REGISTRY_NAME=your-registry-name"
                return 1
            fi
            full_image_name="${AZURE_REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${VERSION}"
            
            # Login to ACR
            print_status "Logging in to Azure Container Registry..."
            az acr login --name ${AZURE_REGISTRY_NAME}
            
            docker tag ${IMAGE_NAME}:${VERSION} ${full_image_name}
            print_status "Pushing to Azure Container Registry..."
            docker push ${full_image_name}
            ;;
            
        "custom")
            if [ -z "$CUSTOM_REGISTRY" ]; then
                print_error "CUSTOM_REGISTRY environment variable not set"
                print_warning "Please set: export CUSTOM_REGISTRY=your-registry.com"
                return 1
            fi
            full_image_name="${CUSTOM_REGISTRY}/${IMAGE_NAME}:${VERSION}"
            docker tag ${IMAGE_NAME}:${VERSION} ${full_image_name}
            print_status "Pushing to custom registry..."
            docker push ${full_image_name}
            ;;
            
        *)
            print_error "Unknown registry: $registry"
            print_warning "Available options: dockerhub, ecr, gcr, acr, custom"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_status "Successfully pushed to registry: ${full_image_name}"
        echo -e "${BLUE}=== Image Details ===${NC}"
        echo "Registry: $registry"
        echo "Image: $full_image_name"
        echo "Version: $VERSION"
        echo ""
        echo -e "${YELLOW}Update your Kubernetes deployment to use:${NC}"
        echo "image: $full_image_name"
        return 0
    else
        print_error "Failed to push to registry: $registry"
        return 1
    fi
}

# Main execution
if [ -n "$REGISTRY" ]; then
    print_status "Pushing to registry: $REGISTRY"
    push_to_registry $REGISTRY
else
    echo -e "${BLUE}=== Registry Options ===${NC}"
    echo "1. Docker Hub (dockerhub)"
    echo "2. Amazon ECR (ecr)"
    echo "3. Google Container Registry (gcr)"
    echo "4. Azure Container Registry (acr)"
    echo "5. Custom Registry (custom)"
    echo ""
    echo -e "${YELLOW}Usage examples:${NC}"
    echo "./build-and-deploy.sh latest dockerhub"
    echo "./build-and-deploy.sh v1.0.0 ecr"
    echo "./build-and-deploy.sh latest gcr"
    echo ""
    echo -e "${YELLOW}Required environment variables:${NC}"
    echo "Docker Hub: DOCKERHUB_USERNAME"
    echo "Amazon ECR: AWS_REGION, AWS_ACCOUNT_ID"
    echo "Google GCR: GCP_PROJECT_ID"
    echo "Azure ACR: AZURE_REGISTRY_NAME"
    echo "Custom: CUSTOM_REGISTRY"
    echo ""
    echo -e "${GREEN}Image built successfully: ${IMAGE_NAME}:${VERSION}${NC}"
    echo "Run with registry option to push: ./build-and-deploy.sh $VERSION <registry>"
fi 