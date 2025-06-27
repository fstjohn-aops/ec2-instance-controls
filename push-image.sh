#!/bin/bash

# Check if tag parameter is provided
if [ -z "$1" ]; then
    echo "No tag provided. Available tags in registry:"
    REGISTRY=${REGISTRY:-"cr.aops.tools/aops-docker-repo"}
    podman search --list-tags $REGISTRY/ec2-instance-controls 2>/dev/null | grep -v "TAG" | head -20
    echo ""
    echo "Usage: $0 <tag>"
    echo "Example: $0 v1.0.0"
    exit 1
fi

TAG=$1
REGISTRY=${REGISTRY:-"cr.aops.tools/aops-docker-repo"}  # Updated registry URL

# Build the image
echo "Building image with tag: $TAG"
./build-image.sh $TAG

# Tag for registry
echo "Tagging for registry..."
podman tag ec2-instance-controls:$TAG $REGISTRY/ec2-instance-controls:$TAG

# Push to registry
echo "Pushing to registry..."
podman push $REGISTRY/ec2-instance-controls:$TAG

echo "Image pushed: $REGISTRY/ec2-instance-controls:$TAG" 