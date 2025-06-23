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
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize AWS EC2 client
ec2_client = boto3.client('ec2', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Database setup
def init_db():
    """Initialize SQLite database with user-instance mappings"""
    conn = sqlite3.connect('ec2_instances.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slack_user_id TEXT UNIQUE NOT NULL,
            slack_username TEXT NOT NULL,
            instance_id TEXT UNIQUE NOT NULL,
            instance_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user_instance(slack_user_id):
    """Get instance ID for a given Slack user"""
    conn = sqlite3.connect('ec2_instances.db')
    cursor = conn.cursor()
    cursor.execute('SELECT instance_id, instance_name FROM user_instances WHERE slack_user_id = ?', (slack_user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def create_user_instance_mapping(slack_user_id, slack_username, instance_id, instance_name):
    """Create or update user-instance mapping"""
    conn = sqlite3.connect('ec2_instances.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_instances 
        (slack_user_id, slack_username, instance_id, instance_name, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (slack_user_id, slack_username, instance_id, instance_name, datetime.now()))
    conn.commit()
    conn.close()

# EC2 instance management functions
def get_instance_status(instance_id):
    """Get current status of an EC2 instance"""
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
    try:
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        return response['StartingInstances'][0]['CurrentState']['Name']
    except ClientError as e:
        logger.error(f"Error starting instance: {e}")
        raise

def stop_instance(instance_id):
    """Stop an EC2 instance"""
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        return response['StoppingInstances'][0]['CurrentState']['Name']
    except ClientError as e:
        logger.error(f"Error stopping instance: {e}")
        raise

# Slack slash command handlers
@slack_app.command("/ec2-start")
def handle_start_command(ack, respond, command):
    """Handle /ec2-start command"""
    ack()
    user_id = command['user_id']
    username = command['user_name']
    
    # Get user's instance
    user_instance = get_user_instance(user_id)
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
    user_instance = get_user_instance(user_id)
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
    user_instance = get_user_instance(user_id)
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
    conn = sqlite3.connect('ec2_instances.db')
    cursor = conn.cursor()
    cursor.execute('SELECT slack_user_id, slack_username, instance_id, instance_name, created_at FROM user_instances')
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

@app.route('/api/assign-instance', methods=['POST'])
def assign_instance():
    """Assign an EC2 instance to a Slack user"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['slack_user_id', 'slack_username', 'instance_id']):
        return jsonify({"error": "Missing required fields: slack_user_id, slack_username, instance_id"}), 400
    
    try:
        # Verify instance exists
        response = ec2_client.describe_instances(InstanceIds=[data['instance_id']])
        if not response['Reservations']:
            return jsonify({"error": "Instance not found"}), 404
        
        instance_name = response['Reservations'][0]['Instances'][0].get('Tags', [])
        instance_name = next((tag['Value'] for tag in instance_name if tag['Key'] == 'Name'), data['instance_id'])
        
        # Create mapping
        create_user_instance_mapping(
            data['slack_user_id'],
            data['slack_username'],
            data['instance_id'],
            instance_name
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
    conn = sqlite3.connect('ec2_instances.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_instances WHERE slack_user_id = ?', (slack_user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted:
        return jsonify({"message": "Assignment removed successfully"})
    else:
        return jsonify({"error": "Assignment not found"}), 404

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

# Slack request handler
handler = SlackRequestHandler(slack_app)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    return handler.handle(request)

@app.route("/slack/install", methods=["GET"])
def install():
    """Handle Slack app installation"""
    return handler.handle(request)

@app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    """Handle OAuth redirect"""
    return handler.handle(request)

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 