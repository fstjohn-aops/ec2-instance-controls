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