# EC2 Instance Control Slack Bot

A Flask-based Slack bot that allows users to control their assigned EC2 instances through Slack commands.

## Features

- **One-to-one user-instance mapping**: Each user can only control their assigned EC2 instance
- **Simple Slack commands**: Start, stop, and check status of instances
- **RESTful API**: Admin endpoints for managing user-instance assignments
- **Containerized deployment**: Ready for Docker/Kubernetes deployment
- **SQLite database**: Lightweight storage for user-instance mappings

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- AWS account with EC2 instances
- Slack workspace with admin permissions

### 2. Environment Setup

Copy the example environment file and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual values:
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_SIGNING_SECRET`: Your Slack app signing secret
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)

### 3. Run with Docker

```bash
docker-compose up --build
```

The API will be available at `http://localhost:5000`

## Slack Bot Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "EC2 Instance Control")
4. Select your workspace

### 2. Configure Bot Token Scopes

In your Slack app settings, go to "OAuth & Permissions" and add these scopes:

**Bot Token Scopes:**
- `app_mentions:read` - Read mentions
- `chat:write` - Send messages
- `commands` - Add slash commands

### 3. Enable Events

1. Go to "Event Subscriptions"
2. Enable events
3. Add your request URL: `https://your-domain.com/slack/events`
4. Subscribe to bot events:
   - `app_mention`

### 4. Add Slash Commands

1. Go to "Slash Commands"
2. Create command:
   - Command: `/ec2-help`
   - Request URL: `https://your-domain.com/slack/events`
   - Description: "Get help with EC2 instance commands"

### 5. Install App

1. Go to "Install App"
2. Click "Install to Workspace"
3. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
4. Copy the "Signing Secret"

### 6. Update Environment Variables

Add these to your `.env` file:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## API Endpoints

### Health Check
```
GET /health
```

### List All Assignments
```
GET /api/assignments
```

### Assign Instance to User
```
POST /api/assign-instance
Content-Type: application/json

{
  "slack_user_id": "U1234567890",
  "slack_username": "john.doe",
  "instance_id": "i-1234567890abcdef0"
}
```

### Remove Assignment
```
DELETE /api/assignments/{slack_user_id}
```

### Get Instance Status
```
GET /api/instances/{instance_id}/status
```

## Slack Bot Usage

### Commands

Users can interact with the bot by mentioning it:

- `@bot start` - Start your assigned instance
- `@bot stop` - Stop your assigned instance  
- `@bot status` - Check instance status
- `/ec2-help` - Get help

### Example Conversations

```
User: @bot start my instance
Bot: Starting your instance web-server-01 (i-1234567890abcdef0)...

User: @bot status
Bot: Your instance web-server-01 (i-1234567890abcdef0) is currently running.
```

## AWS IAM Permissions

Your AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

## Production Deployment

### Kubernetes

Create a deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ec2-slack-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ec2-slack-bot
  template:
    metadata:
      labels:
        app: ec2-slack-bot
    spec:
      containers:
      - name: ec2-slack-bot
        image: your-registry/ec2-slack-bot:latest
        ports:
        - containerPort: 5000
        env:
        - name: SLACK_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: slack-secrets
              key: bot-token
        - name: SLACK_SIGNING_SECRET
          valueFrom:
            secretKeyRef:
              name: slack-secrets
              key: signing-secret
        - name: AWS_REGION
          value: "us-east-1"
        volumeMounts:
        - name: db-storage
          mountPath: /app/ec2_instances.db
          subPath: ec2_instances.db
      volumes:
      - name: db-storage
        persistentVolumeClaim:
          claimName: ec2-bot-pvc
```

### Environment Variables

For production, use Kubernetes secrets or your cloud provider's secret management:

```bash
# Create secrets
kubectl create secret generic slack-secrets \
  --from-literal=bot-token=xoxb-your-token \
  --from-literal=signing-secret=your-secret

kubectl create secret generic aws-credentials \
  --from-literal=access-key-id=your-key \
  --from-literal=secret-access-key=your-secret
```

## Development

### Local Development

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_SIGNING_SECRET=your-secret
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

4. Run the application:
```bash
python app.py
```

### Testing

Test the API endpoints:

```bash
# Health check
curl http://localhost:5000/health

# List assignments
curl http://localhost:5000/api/assignments

# Assign instance
curl -X POST http://localhost:5000/api/assign-instance \
  -H "Content-Type: application/json" \
  -d '{"slack_user_id":"U123","slack_username":"test","instance_id":"i-123"}'
```

### Automated Testing

Before getting Slack app access, you can run comprehensive local tests:

```bash
# Run the test script
./test_local.sh
```

This script tests:
- Docker environment setup
- Environment variable validation
- Container startup and health checks
- API endpoint functionality
- Error handling with invalid data
- Database creation
- Application logs

The test script validates everything except Slack integration, so you can ensure your setup works before asking your admin to install the Slack app.

## Security Considerations

1. **Use IAM roles** instead of access keys in production
2. **Restrict EC2 permissions** to only necessary instances
3. **Use HTTPS** for all external communications
4. **Validate Slack requests** using the signing secret
5. **Rate limit** API endpoints to prevent abuse
6. **Log all actions** for audit purposes

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check Slack app configuration and token
2. **AWS permissions error**: Verify IAM permissions
3. **Instance not found**: Ensure instance ID is correct and accessible
4. **Database errors**: Check file permissions for SQLite database

### Logs

Check application logs:
```bash
docker-compose logs ec2-slack-bot
```

## Future Enhancements

- [ ] User groups and team management
- [ ] Instance scheduling (auto-start/stop)
- [ ] Cost tracking and alerts
- [ ] Multi-region support
- [ ] Instance creation/deletion
- [ ] SSH key management
- [ ] Backup and restore functionality 