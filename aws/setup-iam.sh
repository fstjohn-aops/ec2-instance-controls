#!/bin/bash

# Setup IAM Role and Policy for EKS Service Account
# This script creates the necessary IAM resources for the EC2 controls application

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-west-2}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME}
POLICY_NAME="EC2ControlsPolicy"
ROLE_NAME="ec2-controls-role"
SERVICE_ACCOUNT_NAME="ec2-controls-sa"
NAMESPACE="ec2-controls"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Setting up IAM Role and Policy for EKS Service Account ===${NC}"

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
    
    # Check if eksctl is installed (for OIDC provider setup)
    if ! command -v eksctl &> /dev/null; then
        print_warning "eksctl is not installed. You may need to install it for OIDC provider setup."
        print_warning "Install with: brew install eksctl (macOS) or follow AWS documentation"
    fi
    
    print_status "All prerequisites met!"
}

# Create IAM policy
create_policy() {
    print_status "Creating IAM policy: ${POLICY_NAME}"
    
    # Check if policy already exists
    if aws iam get-policy --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME} &> /dev/null; then
        print_warning "Policy ${POLICY_NAME} already exists. Updating..."
        aws iam create-policy-version \
            --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME} \
            --policy-document file://aws/iam-policy.json \
            --set-as-default
    else
        aws iam create-policy \
            --policy-name ${POLICY_NAME} \
            --policy-document file://aws/iam-policy.json \
            --description "Policy for EC2 Instance Controls application"
    fi
    
    print_status "IAM policy created/updated successfully!"
}

# Setup OIDC provider for EKS
setup_oidc_provider() {
    print_status "Setting up OIDC provider for EKS cluster..."
    
    # Get OIDC provider ID
    OIDC_PROVIDER=$(aws eks describe-cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION} --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
    
    if [ -z "$OIDC_PROVIDER" ]; then
        print_error "Could not get OIDC provider ID from EKS cluster"
        exit 1
    fi
    
    print_status "OIDC Provider ID: ${OIDC_PROVIDER}"
    
    # Check if OIDC provider exists
    if ! aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, '${OIDC_PROVIDER}')]" --output text | grep -q "${OIDC_PROVIDER}"; then
        print_status "Creating OIDC provider..."
        eksctl utils associate-iam-oidc-provider --cluster ${EKS_CLUSTER_NAME} --region ${AWS_REGION} --approve
    else
        print_status "OIDC provider already exists"
    fi
}

# Create IAM role
create_role() {
    print_status "Creating IAM role: ${ROLE_NAME}"
    
    # Get OIDC provider ID
    OIDC_PROVIDER=$(aws eks describe-cluster --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION} --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
    
    # Create trust policy
    cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/oidc.eks.${AWS_REGION}.amazonaws.com/id/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.${AWS_REGION}.amazonaws.com/id/${OIDC_PROVIDER}:sub": "system:serviceaccount:${NAMESPACE}:${SERVICE_ACCOUNT_NAME}",
          "oidc.eks.${AWS_REGION}.amazonaws.com/id/${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF
    
    # Check if role already exists
    if aws iam get-role --role-name ${ROLE_NAME} &> /dev/null; then
        print_warning "Role ${ROLE_NAME} already exists. Updating trust policy..."
        aws iam update-assume-role-policy \
            --role-name ${ROLE_NAME} \
            --policy-document file:///tmp/trust-policy.json
    else
        aws iam create-role \
            --role-name ${ROLE_NAME} \
            --assume-role-policy-document file:///tmp/trust-policy.json \
            --description "Role for EC2 Instance Controls application"
    fi
    
    # Attach policy to role
    print_status "Attaching policy to role..."
    aws iam attach-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}
    
    print_status "IAM role created/updated successfully!"
}

# Show setup summary
show_summary() {
    print_status "IAM Setup Complete!"
    echo ""
    echo -e "${BLUE}=== Summary ===${NC}"
    echo "Policy: arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"
    echo "Role: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
    echo "Service Account: ${SERVICE_ACCOUNT_NAME}"
    echo "Namespace: ${NAMESPACE}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update k8s/deployment.yaml with your AWS account ID"
    echo "2. Update k8s/service-account.yaml with your AWS account ID"
    echo "3. Run the deployment script: ./eks-ecr-deploy.sh"
    echo ""
    echo -e "${GREEN}The role ARN to use in your manifests:${NC}"
    echo "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
}

# Cleanup temporary files
cleanup() {
    rm -f /tmp/trust-policy.json
}

# Main execution
main() {
    check_prerequisites
    create_policy
    setup_oidc_provider
    create_role
    show_summary
    cleanup
}

# Run main function
main 