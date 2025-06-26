The deployment to Kubernetes is done with one command:

    kubectl apply -f k8s/

To build and push a new image version:

    # Build and push to registry
    ./push-image.sh v1.0.0

To update the running container with a new image, the `update-deployment.sh` script makes it easy to call out a new (or old, if rolling back) image version:

    # Update to container version v1.0.0
    ./update-deployment.sh v1.0.0

## Background
This is a Slack bot for controlling EC2 instances. Several k8s resources are created:
- `00-namespace`:  A Namespace to house this Slack bot and all supporting services
- `01-deployment`: Describe how the Slack bot containers are run using a Deployment.
- `02-service`: Create a Service for the Slack bot Deployment.
- `03-ingress`: Use Ingress to allow external network traffic to reach the Slack bot Service.
- `04-configmap`: Configuration data for the Slack bot application.

## Container Registry
Images are pulled from: `cr.aops.tool/aops-docker-repo/ec2-instance-controls`