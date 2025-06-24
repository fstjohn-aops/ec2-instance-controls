# EC2 Instance Control App

A simple Flask application for managing EC2 instances via REST API.

## Features

- List EC2 instances
- Get instance status
- Start/stop instances
- Manage instance-user assignments
- Health check endpoint

## Quick Start

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   ./run.sh
   ```
   Or manually:
   ```bash
   python3 app.py
   ```

3. Run tests:
   ```bash
   ./test.sh
   ```

### Docker

1. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Or build and run manually:
   ```bash
   docker build -t ec2-control-app .
   docker run -p 8000:8000 ec2-control-app
   ```

## API Endpoints

- `GET /health` - Health check
- `GET /api/instances` - List all instances
- `GET /api/instances/{id}/status` - Get instance status
- `POST /api/instances/{id}/start` - Start instance
- `POST /api/instances/{id}/stop` - Stop instance
- `GET /api/assignments` - List assignments
- `POST /api/assignments` - Create assignment
- `DELETE /api/assignments/{user_id}` - Delete assignment

## Environment Variables

- `PORT` - Server port (default: 8000)
- `TEST_MODE` - Enable test mode (default: false)
- `DB_PATH` - SQLite database path (default: instances.db)

## Test Mode

Set `TEST_MODE=true` to use mock data instead of real AWS calls. 