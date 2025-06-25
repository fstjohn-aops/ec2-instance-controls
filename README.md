# EC2 Instance Control App

Simple Flask app for managing EC2 instances.

## Setup

1. Copy environment file:
   ```bash
   cp env.example .env
   ```

2. Add your AWS credentials to `.env`:
   ```bash
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. Run:
   ```bash
   python3 app.py
   # or
   docker-compose up
   ```

## Endpoints

- `GET /health` - Health check
- `GET /api/instances` - List instances
- `POST /api/instances/{id}/start` - Start instance
- `POST /api/instances/{id}/stop` - Stop instance
- `POST /api/slack/test` - Test Slack data (logs everything)

## Test Slack

Point your Slack app to `http://your-server:8000/api/slack/test` and check the logs to see what data Slack sends. 

## Todo

- Add group RBAC
- Add default instance ID for some users
   - so they can just `/ec2-instance-power on`
- Use tags instead?
- Allow users to use IP address and other identifiers
- Set up SSL on the server
- Limit server IPs
- Add admin endpoints for managing permissions from slack
- Integrate with teleport for groups implementation
   - do we then also have owners for each instance? i'd rather have one method 
   for everything, maybe an hourly sync with teleport groups and then that is
   reduced or consolidated into an ec2 instance -> list of users map
- Get this running on K8s
- Allow users to wrap stuff in quotes as well