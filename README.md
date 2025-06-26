# EC2 Instance Control App

A Flask application for managing EC2 instances through Slack integration. Users can check instance status, start/stop instances, and list their assigned instances.

## Features

- **Instance Status Check**: Get current state of EC2 instances
- **Power Control**: Start or stop EC2 instances
- **User Permissions**: Role-based access control with admin and user roles
- **Slack Integration**: Responds with ephemeral messages for clean UX
- **Health Monitoring**: Health check endpoint for monitoring

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
- **Function**: Lists all instances assigned to the user with their current states

### Admin Check
- **Endpoint**: `POST /admin/check`
- **Parameters**: `user_id`, `user_name`
- **Function**: Checks if a user has admin privileges

### EC2 Power Control
- **Endpoints**: `POST /ec2/power` or `POST /ec2-power-state`
- **Parameters**: `user_id`, `text`
- **Text Format**: 
  - `i-1234567890abcdef0` - Check instance status
  - `i-1234567890abcdef0 on` - Start instance
  - `i-1234567890abcdef0 off` - Stop instance

### EC2 Schedule Control
- **Endpoint**: `POST /ec2-schedule`
- **Parameters**: `user_id`, `text`
- **Text Format**: 
  - `i-1234567890abcdef0` - Check instance schedule
  - `i-1234567890abcdef0 9am to 5pm` - Set schedule (start at 9 AM, stop at 5 PM)
  - `i-1234567890abcdef0 5:30am to 17:30` - Set schedule with various time formats
- **Time Formats Supported**:
  - `5am`, `5:00am`, `5:00 am`, `5:00 Am` - All equivalent
  - `5pm`, `5:30pm`, `17:00`, `17:30` - 12-hour and 24-hour formats
  - Flexible parsing using python-dateutil library

**Usage:** `/ec2-schedule <instance> [<start> to <stop>]`

## User Permissions

The application uses a role-based access control system:

- **Admin Users**: Can control any instance (configured in `src/config.py`)
- **Regular Users**: Can only control their assigned instances
- **Instance Assignment**: Users are mapped to specific EC2 instances in the configuration

## Testing

Run the test suite:
```bash
./test.sh
```

## Configuration

### User Management
Edit `src/config.py` to:
- Add/remove admin users
- Assign EC2 instances to users
- Configure AWS region

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
│   ├── auth.py         # User authentication and permissions
│   ├── aws_client.py   # AWS EC2 operations
│   ├── config.py       # Configuration and user mappings
│   └── handlers.py     # Request handlers
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

- Add group RBAC
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
