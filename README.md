# EC2 Instance Control App

A Flask application for managing EC2 instances through Slack integration. Any authenticated Slack user can check instance status, start/stop instances, and list all instances in the AWS region.

## Features

- **Instance Status Check**: Get current state of EC2 instances
- **Power Control**: Start or stop EC2 instances
- **Universal Access**: Any authenticated Slack user can manage all instances
- **Slack Integration**: Responds with ephemeral messages for clean UX
- **Health Monitoring**: Health check endpoint for monitoring
- **Instance Scheduling**: Set automatic start/stop schedules for instances

## Setup

### Quick Setup

1. Clone the repository and navigate to the directory:
   ```bash
   cd ec2-instance-controls
   ```

2. Run the setup script to create a virtual environment and install dependencies:
   ```bash
   ./setup.sh
   ```

3. Copy environment file:
   ```bash
   cp env.example .env
   ```

4. Configure your environment variables in `.env`:
   ```bash
   # AWS Configuration
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_REGION=us-west-2
   
   # Slack Configuration (if using Slack integration)
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   SLACK_SIGNING_SECRET=your_slack_signing_secret
   ```

5. Run the application:
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Run the app
   python3 app.py
   # or use the run script
   ./run.sh
   ```

### Docker Setup

Alternatively, you can run with Docker:
```bash
docker-compose up
```

## API Endpoints

All endpoints accept POST requests with form data.

### Health Check
- **Endpoint**: `GET /health`
- **Response**: `{"status": "ok"}`

### Instance Management
- **Endpoint**: `POST /instances`
- **Parameters**: `user_id`, `user_name`
- **Function**: Lists all instances in the AWS region with their current states

### Authentication Check
- **Endpoint**: `POST /admin/check`
- **Parameters**: `user_id`, `user_name`
- **Function**: Verifies if a user is authenticated and can access instances

### EC2 Power Control
- **Endpoints**: `POST /ec2/power` or `POST /ec2-power-state`
- **Parameters**: `user_id`, `text`
- **Text Format**: 
  - `i-1234567890abcdef0` - Check instance status
  - `i-1234567890abcdef0 on` - Start instance
  - `i-1234567890abcdef0 off` - Stop instance
  - `instance-name` - Use instance name instead of ID
  - `instance-name on` - Start instance by name

### EC2 Schedule Control
- **Endpoint**: `POST /ec2-schedule`
- **Parameters**: `user_id`, `text`
- **Text Format**: 
  - `i-1234567890abcdef0` - Check instance schedule
  - `i-1234567890abcdef0 9am to 5pm` - Set schedule (start at 9 AM, stop at 5 PM)
  - `i-1234567890abcdef0 5:30am to 17:30` - Set schedule with various time formats
  - `i-1234567890abcdef0 clear` - Clear/remove schedule
- **Time Formats Supported**:
  - `5am`, `5:00am`, `5:00 am`, `5:00 Am` - All equivalent
  - `5pm`, `5:30pm`, `17:00`, `17:30` - 12-hour and 24-hour formats
  - Flexible parsing using python-dateutil library
- **Clear Commands**: `clear`, `reset`, `unset`, `no`, `remove`, `delete` (all equivalent)

**Usage:** `/ec2-schedule <instance> [<start> to <stop>]` or `/ec2-schedule <instance> clear`

## Access Control

The application uses a simplified access control system:

- **Authentication Required**: Users must be logged into Slack and provide a `user_id`
- **Universal Access**: Any authenticated user can manage all EC2 instances in the configured AWS region
- **No User Restrictions**: No role-based permissions or instance assignments - all users have equal access

## Testing

Run the test suite:
```bash
./test.sh
```

## Configuration

### AWS Configuration
Edit `src/config.py` to:
- Configure AWS region
- Set default region for EC2 operations

### AWS Permissions
The application requires the following AWS permissions:
- `ec2:DescribeInstances`
- `ec2:StartInstances`
- `ec2:StopInstances`

## Development

### Project Structure
```
ec2-instance-controls/
├── app.py              # Main Flask application
├── src/
│   ├── auth.py         # User authentication (simplified)
│   ├── aws_client.py   # AWS EC2 operations
│   ├── config.py       # Configuration (AWS region only)
│   ├── handlers.py     # Request handlers
│   └── schedule.py     # Instance scheduling
├── test/               # Test files
├── requirements.txt    # Python dependencies
└── setup.sh           # Setup script
```

### Adding New Features
1. Add new handlers in `src/handlers.py`
2. Add corresponding routes in `app.py`
3. Update tests in `test/test_handlers.py`
4. Update this README

## Todo

- Add group RBAC (if needed in the future)
- Add default instance ID for some users
- Use tags instead of hardcoded instance IDs
- Allow users to use IP address and other identifiers
- Set up SSL on the server
- Limit server IPs
- Add admin endpoints for managing permissions from slack
- Integrate with teleport for groups implementation
- Add logic to prevent spam with power state changes
- Make it dynamically load data (use a database)
- Use production WSGI server
- Add logic to regularly check if EC2 instances still exist

## Possible Implementations for Groups

- Teleport OAuth?
- Slack channels? give private pod channels control over their instances
- manually set up in a database

## Possible Implementations for Scheduled Power State

- AWS EC2 instance scheduler
- ~~Homemade CRON or something~~ (Implemented: Basic schedule storage and parsing)
