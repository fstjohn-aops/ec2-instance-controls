import os
import logging
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import boto3
from botocore.exceptions import ClientError
import sqlite3
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack app
slack_token = os.environ.get("SLACK_BOT_TOKEN")
slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")

# Only initialize Slack app if we have valid credentials
if slack_token and slack_signing_secret and not slack_token.startswith("xoxb-your"):
    try:
        slack_app = App(
            token=slack_token,
            signing_secret=slack_signing_secret
        )
        slack_handler = SlackRequestHandler(slack_app)
    except Exception as e:
        logger.warning(f"Failed to initialize Slack app: {e}")
        slack_app = None
        slack_handler = None
else:
    logger.warning("Slack credentials not properly configured. Slack functionality disabled.")
    slack_app = None
    slack_handler = None

# Initialize AWS EC2 client
ec2_client = boto3.client('ec2', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Test mode flag
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

# Mock instance states for test mode
MOCK_INSTANCE_STATES = {
    'i-0ecdfc9a2e3e53302': 'running',
    'i-test-instance-1': 'stopped',
    'i-test-instance-2': 'running',
    'i-test-instance-3': 'stopped'
}

# Database setup
def init_db():
    """Initialize SQLite database with instance-user mappings"""
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instance_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT UNIQUE NOT NULL,
                instance_name TEXT,
                slack_user_id TEXT NOT NULL,
                slack_username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_instance_for_user(slack_user_id):
    """Get instance ID for a given Slack user"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT instance_id, instance_name FROM instance_users WHERE slack_user_id = ?', (slack_user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Database error in get_instance_for_user: {e}")
        return None

def get_users_for_instance(instance_id):
    """Get all users that can control a given instance"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT slack_user_id, slack_username FROM instance_users WHERE instance_id = ?', (instance_id,))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Database error in get_users_for_instance: {e}")
        return []

def create_instance_user_mapping(instance_id, instance_name, slack_user_id, slack_username):
    """Create or update instance-user mapping"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO instance_users 
            (instance_id, instance_name, slack_user_id, slack_username, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (instance_id, instance_name, slack_user_id, slack_username, datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database error in create_instance_user_mapping: {e}")
        raise

def can_user_control_instance(slack_user_id, instance_id):
    """Check if a user can control a specific instance"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM instance_users WHERE slack_user_id = ? AND instance_id = ?', (slack_user_id, instance_id))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Database error in can_user_control_instance: {e}")
        return False

# EC2 instance management functions
def get_instance_status(instance_id):
    """Get current status of an EC2 instance"""
    if TEST_MODE:
        # Return mock status in test mode
        return MOCK_INSTANCE_STATES.get(instance_id, 'unknown')
    
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if response['Reservations']:
            instance = response['Reservations'][0]['Instances'][0]
            return instance['State']['Name']
        return None
    except ClientError as e:
        logger.error(f"Error getting instance status: {e}")
        return None

def start_instance(instance_id):
    """Start an EC2 instance"""
    if TEST_MODE:
        # Simulate starting in test mode
        if instance_id in MOCK_INSTANCE_STATES:
            MOCK_INSTANCE_STATES[instance_id] = 'running'
            logger.info(f"TEST MODE: Started instance {instance_id}")
            return 'running'
        return 'unknown'
    
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        return response['StartingInstances'][0]['CurrentState']['Name']
    except ClientError as e:
        logger.error(f"Error starting instance: {e}")
        raise

def stop_instance(instance_id):
    """Stop an EC2 instance"""
    if TEST_MODE:
        # Simulate stopping in test mode
        if instance_id in MOCK_INSTANCE_STATES:
            MOCK_INSTANCE_STATES[instance_id] = 'stopped'
            logger.info(f"TEST MODE: Stopped instance {instance_id}")
            return 'stopped'
        return 'unknown'
    
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        return response['StoppingInstances'][0]['CurrentState']['Name']
    except ClientError as e:
        logger.error(f"Error stopping instance: {e}")
        raise

# Slack slash command handlers
if slack_app:
    @slack_app.command("/ec2-start")
    def handle_start_command(ack, respond, command):
        """Handle /ec2-start command"""
        ack()
        user_id = command['user_id']
        username = command['user_name']
        
        # Get user's instance
        user_instance = get_instance_for_user(user_id)
        if not user_instance:
            respond(f"You don't have an EC2 instance assigned yet. Please contact an administrator.")
            return
        
        instance_id, instance_name = user_instance
        
        try:
            current_status = get_instance_status(instance_id)
            if current_status == 'running':
                respond(f"Your instance {instance_name} ({instance_id}) is already running!")
            elif current_status == 'stopped':
                start_instance(instance_id)
                respond(f"Starting your instance {instance_name} ({instance_id})...")
            else:
                respond(f"Your instance {instance_name} ({instance_id}) is in {current_status} state. Please wait for it to be stopped before starting.")
        except Exception as e:
            respond(f"Error starting your instance: {str(e)}")

    @slack_app.command("/ec2-stop")
    def handle_stop_command(ack, respond, command):
        """Handle /ec2-stop command"""
        ack()
        user_id = command['user_id']
        username = command['user_name']
        
        # Get user's instance
        user_instance = get_instance_for_user(user_id)
        if not user_instance:
            respond(f"You don't have an EC2 instance assigned yet. Please contact an administrator.")
            return
        
        instance_id, instance_name = user_instance
        
        try:
            current_status = get_instance_status(instance_id)
            if current_status == 'stopped':
                respond(f"Your instance {instance_name} ({instance_id}) is already stopped!")
            elif current_status == 'running':
                stop_instance(instance_id)
                respond(f"Stopping your instance {instance_name} ({instance_id})...")
            else:
                respond(f"Your instance {instance_name} ({instance_id}) is in {current_status} state. Please wait for it to be running before stopping.")
        except Exception as e:
            respond(f"Error stopping your instance: {str(e)}")

    @slack_app.command("/ec2-status")
    def handle_status_command(ack, respond, command):
        """Handle /ec2-status command"""
        ack()
        user_id = command['user_id']
        username = command['user_name']
        
        # Get user's instance
        user_instance = get_instance_for_user(user_id)
        if not user_instance:
            respond(f"You don't have an EC2 instance assigned yet. Please contact an administrator.")
            return
        
        instance_id, instance_name = user_instance
        
        try:
            current_status = get_instance_status(instance_id)
            respond(f"Your instance {instance_name} ({instance_id}) is currently {current_status}.")
        except Exception as e:
            respond(f"Error getting instance status: {str(e)}")

    @slack_app.command("/ec2-help")
    def handle_help_command(ack, respond):
        """Handle /ec2-help command"""
        ack()
        help_text = """
*EC2 Instance Control Commands*

• `/ec2-start` - Start your assigned instance
• `/ec2-stop` - Stop your assigned instance  
• `/ec2-status` - Check instance status
• `/ec2-help` - Show this help message

*Admin Commands* (via API):
• Assign instance to user: `POST /api/assign-instance`
• List all assignments: `GET /api/assignments`
• Remove assignment: `DELETE /api/assignments/{user_id}`
        """
        respond(help_text)

# Flask API endpoints
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/assignments', methods=['GET'])
def list_assignments():
    """List all user-instance assignments"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT slack_user_id, slack_username, instance_id, instance_name, created_at FROM instance_users')
        results = cursor.fetchall()
        conn.close()
        
        assignments = []
        for row in results:
            assignments.append({
                'slack_user_id': row[0],
                'slack_username': row[1],
                'instance_id': row[2],
                'instance_name': row[3],
                'created_at': row[4]
            })
        
        return jsonify(assignments)
    except Exception as e:
        logger.error(f"Error in list_assignments: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

@app.route('/api/assign-instance', methods=['POST'])
def assign_instance():
    """Assign an EC2 instance to a Slack user"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['slack_user_id', 'slack_username', 'instance_id']):
        return jsonify({"error": "Missing required fields: slack_user_id, slack_username, instance_id"}), 400
    
    try:
        instance_name = data.get('instance_name', data['instance_id'])
        
        # In test mode, skip AWS validation for test instances
        if not TEST_MODE or not data['instance_id'].startswith('i-test-'):
            # Verify instance exists in AWS
            response = ec2_client.describe_instances(InstanceIds=[data['instance_id']])
            if not response['Reservations']:
                return jsonify({"error": "Instance not found"}), 404
            
            # Get instance name from AWS tags
            instance_tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
            instance_name = next((tag['Value'] for tag in instance_tags if tag['Key'] == 'Name'), data['instance_id'])
        
        # Create mapping
        create_instance_user_mapping(
            data['instance_id'],
            instance_name,
            data['slack_user_id'],
            data['slack_username']
        )
        
        return jsonify({
            "message": "Instance assigned successfully",
            "slack_user_id": data['slack_user_id'],
            "instance_id": data['instance_id'],
            "instance_name": instance_name
        })
    
    except ClientError as e:
        return jsonify({"error": f"AWS error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/api/assignments/<slack_user_id>', methods=['DELETE'])
def remove_assignment(slack_user_id):
    """Remove user-instance assignment"""
    try:
        data_dir = os.path.join(os.getcwd(), 'data')
        db_path = os.path.join(data_dir, 'ec2_instances.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM instance_users WHERE slack_user_id = ?', (slack_user_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted:
            return jsonify({"message": "Assignment removed successfully"})
        else:
            return jsonify({"error": "Assignment not found"}), 404
    except Exception as e:
        logger.error(f"Error in remove_assignment: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500

@app.route('/api/instances/<instance_id>/status', methods=['GET'])
def get_instance_status_api(instance_id):
    """Get instance status via API"""
    try:
        status = get_instance_status(instance_id)
        if status:
            return jsonify({"instance_id": instance_id, "status": status})
        else:
            return jsonify({"error": "Instance not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Simulation endpoints for testing Slack-like requests
@app.route('/api/simulate/slack/start', methods=['POST'])
def simulate_slack_start():
    """Simulate a Slack /ec2-start command"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Missing user_id"}), 400
    
    user_id = data['user_id']
    
    # Get user's instance
    user_instance = get_instance_for_user(user_id)
    if not user_instance:
        return jsonify({
            "response": f"You don't have an EC2 instance assigned yet. Please contact an administrator.",
            "success": False
        })
    
    instance_id, instance_name = user_instance
    
    try:
        current_status = get_instance_status(instance_id)
        if current_status == 'running':
            return jsonify({
                "response": f"Your instance {instance_name} ({instance_id}) is already running!",
                "success": True,
                "instance_id": instance_id,
                "status": current_status
            })
        elif current_status == 'stopped':
            new_status = start_instance(instance_id)
            return jsonify({
                "response": f"Starting your instance {instance_name} ({instance_id})...",
                "success": True,
                "instance_id": instance_id,
                "old_status": current_status,
                "new_status": new_status
            })
        else:
            return jsonify({
                "response": f"Your instance {instance_name} ({instance_id}) is in {current_status} state. Please wait for it to be stopped before starting.",
                "success": False,
                "instance_id": instance_id,
                "status": current_status
            })
    except Exception as e:
        return jsonify({
            "response": f"Error starting your instance: {str(e)}",
            "success": False,
            "error": str(e)
        })

@app.route('/api/simulate/slack/stop', methods=['POST'])
def simulate_slack_stop():
    """Simulate a Slack /ec2-stop command"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Missing user_id"}), 400
    
    user_id = data['user_id']
    
    # Get user's instance
    user_instance = get_instance_for_user(user_id)
    if not user_instance:
        return jsonify({
            "response": f"You don't have an EC2 instance assigned yet. Please contact an administrator.",
            "success": False
        })
    
    instance_id, instance_name = user_instance
    
    try:
        current_status = get_instance_status(instance_id)
        if current_status == 'stopped':
            return jsonify({
                "response": f"Your instance {instance_name} ({instance_id}) is already stopped!",
                "success": True,
                "instance_id": instance_id,
                "status": current_status
            })
        elif current_status == 'running':
            new_status = stop_instance(instance_id)
            return jsonify({
                "response": f"Stopping your instance {instance_name} ({instance_id})...",
                "success": True,
                "instance_id": instance_id,
                "old_status": current_status,
                "new_status": new_status
            })
        else:
            return jsonify({
                "response": f"Your instance {instance_name} ({instance_id}) is in {current_status} state. Please wait for it to be running before stopping.",
                "success": False,
                "instance_id": instance_id,
                "status": current_status
            })
    except Exception as e:
        return jsonify({
            "response": f"Error stopping your instance: {str(e)}",
            "success": False,
            "error": str(e)
        })

@app.route('/api/simulate/slack/status', methods=['POST'])
def simulate_slack_status():
    """Simulate a Slack /ec2-status command"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Missing user_id"}), 400
    
    user_id = data['user_id']
    
    # Get user's instance
    user_instance = get_instance_for_user(user_id)
    if not user_instance:
        return jsonify({
            "response": f"You don't have an EC2 instance assigned yet. Please contact an administrator.",
            "success": False
        })
    
    instance_id, instance_name = user_instance
    
    try:
        current_status = get_instance_status(instance_id)
        return jsonify({
            "response": f"Your instance {instance_name} ({instance_id}) is currently {current_status}.",
            "success": True,
            "instance_id": instance_id,
            "status": current_status
        })
    except Exception as e:
        return jsonify({
            "response": f"Error getting instance status: {str(e)}",
            "success": False,
            "error": str(e)
        })

@app.route('/api/simulate/slack/start-specific', methods=['POST'])
def simulate_slack_start_specific():
    """Simulate a Slack command to start a specific instance (tests permissions)"""
    data = request.get_json()
    if not data or 'user_id' not in data or 'instance_id' not in data:
        return jsonify({"error": "Missing user_id or instance_id"}), 400
    
    user_id = data['user_id']
    instance_id = data['instance_id']
    
    # Check if user can control this instance
    if not can_user_control_instance(user_id, instance_id):
        return jsonify({
            "response": f"You don't have permission to control instance {instance_id}.",
            "success": False,
            "instance_id": instance_id,
            "user_id": user_id
        })
    
    try:
        current_status = get_instance_status(instance_id)
        if current_status == 'running':
            return jsonify({
                "response": f"Instance {instance_id} is already running!",
                "success": True,
                "instance_id": instance_id,
                "status": current_status
            })
        elif current_status == 'stopped':
            new_status = start_instance(instance_id)
            return jsonify({
                "response": f"Starting instance {instance_id}...",
                "success": True,
                "instance_id": instance_id,
                "old_status": current_status,
                "new_status": new_status
            })
        else:
            return jsonify({
                "response": f"Instance {instance_id} is in {current_status} state. Please wait for it to be stopped before starting.",
                "success": False,
                "instance_id": instance_id,
                "status": current_status
            })
    except Exception as e:
        return jsonify({
            "response": f"Error starting instance {instance_id}: {str(e)}",
            "success": False,
            "error": str(e)
        })

# Slack request handler
@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    if slack_handler:
        return slack_handler.handle(request)
    else:
        return jsonify({"error": "Slack not configured"}), 503

@app.route("/slack/install", methods=["GET"])
def install():
    """Handle Slack app installation"""
    if slack_handler:
        return slack_handler.handle(request)
    else:
        return jsonify({"error": "Slack not configured"}), 503

@app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    """Handle OAuth redirect"""
    if slack_handler:
        return slack_handler.handle(request)
    else:
        return jsonify({"error": "Slack not configured"}), 503

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 