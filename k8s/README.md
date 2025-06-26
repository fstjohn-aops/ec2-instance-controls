The deployment to Kubernetes is done with one command:

    kubectl apply -f k8s/

To update the running container with a new image, the `update-deployment.sh` script makes it easy to call out a new (or old, if rolling back) image version:

    # Update to container version 14
    ./update-deployment.sh 14

## Background
This is a Slack bot for controlling EC2 instances. Several k8s resources are created:
- `00-namespace`:  A Namespace to house this Slack bot and all supporting services
- `01-deployment`: Describe how the Slack bot containers are run using a Deployment.
- `02-service`: Create a Service for the Slack bot Deployment.
- `03-ingress`: Use Ingress to allow external network traffic to reach the Slack bot Service.
- `04-configmap`: Configuration data for the Slack bot application.