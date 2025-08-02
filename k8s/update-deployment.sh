#!/bin/bash

set -e

# --- Configuration ---
REGISTRY="cr.aops.tools/aops-docker-repo"
IMAGE_NAME="ec2-instance-controls"
K8S_NAMESPACE="ec2-slack-bot"
K8S_RESOURCE_TYPE="deployment"
K8S_RESOURCE_NAME="ec2-slack-bot"
K8S_CONTAINER_NAME="ec2-slack-bot"
# ---------------------

LATEST_TAG=$1

if [ -z "$LATEST_TAG" ]; then
  echo "Usage: $0 <latest-tag>"
  exit 1
fi

echo "Updating $K8S_RESOURCE_NAME $K8S_RESOURCE_TYPE to image tag: $LATEST_TAG"

# Update the resource with the new image
kubectl -n $K8S_NAMESPACE \
  set image ${K8S_RESOURCE_TYPE}/${K8S_RESOURCE_NAME} \
  ${K8S_CONTAINER_NAME}=${REGISTRY}/${IMAGE_NAME}:${LATEST_TAG}

# Wait for rollout to complete
echo "Waiting for deployment to roll out..."
kubectl -n $K8S_NAMESPACE rollout status ${K8S_RESOURCE_TYPE}/${K8S_RESOURCE_NAME}

echo "Deployment successfully updated and rolled out!"

# Optional: Display the new pod status
echo -e "\nNew pod status:"
kubectl -n $K8S_NAMESPACE get pods -l app=$K8S_RESOURCE_NAME