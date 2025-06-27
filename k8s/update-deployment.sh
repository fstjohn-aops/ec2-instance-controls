#!/bin/bash

set -e

LATEST_TAG=$1

if [ -z "$LATEST_TAG" ]; then
  echo "Usage: $0 <latest-tag>"
  exit 1
fi

echo "Updating ec2-slack-bot deployment to image tag: $LATEST_TAG"

# Update the deployment with new image
kubectl -n ec2-slack-bot set image deployment/ec2-slack-bot ec2-slack-bot=cr.aops.tools/aops-docker-repo/ec2-instance-controls:$LATEST_TAG

# Wait for rollout to complete
echo "Waiting for deployment to roll out..."
kubectl -n ec2-slack-bot rollout status deployment/ec2-slack-bot

echo "Deployment successfully updated and rolled out!"

# Optional: Display the new pod status
echo -e "\nNew pod status:"
kubectl -n ec2-slack-bot get pods -l app=ec2-slack-bot