#!/usr/bin/env python3
"""
Simple EC2 Instance Control Flask App
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = int(os.environ.get('PORT', 8000))
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

# Initialize AWS client
ec2_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    try:
        import boto3
        ec2_client = boto3.client(
            'ec2',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        logger.info("AWS client initialized")
    except Exception as e:
        logger.error(f"AWS client failed: {e}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'aws_connected': ec2_client is not None
    })

@app.route('/api/instances', methods=['GET'])
def list_instances():
    """List all instances"""
    if not ec2_client:
        return jsonify({'error': 'AWS not configured'}), 500
    
    try:
        response = ec2_client.describe_instances()
        instances = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                name = 'Unnamed'
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                
                instances.append({
                    'id': instance['InstanceId'],
                    'name': name,
                    'state': instance['State']['Name']
                })
        
        return jsonify({'instances': instances})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instances/<instance_id>/start', methods=['POST'])
def start_instance(instance_id):
    """Start an instance"""
    if not ec2_client:
        return jsonify({'error': 'AWS not configured'}), 500
    
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        return jsonify({'message': f'Started {instance_id}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instances/<instance_id>/stop', methods=['POST'])
def stop_instance(instance_id):
    """Stop an instance"""
    if not ec2_client:
        return jsonify({'error': 'AWS not configured'}), 500
    
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        return jsonify({'message': f'Stopped {instance_id}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/slack/test', methods=['POST'])
def slack_test():
    """Test endpoint to see what Slack sends"""
    logger.info("=== SLACK TEST ENDPOINT CALLED ===")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Data: {request.get_data(as_text=True)}")
    
    try:
        data = request.get_json()
        logger.info(f"JSON: {json.dumps(data, indent=2)}")
    except:
        logger.info("Not JSON data")
    
    return jsonify({
        'message': 'Slack data received and logged',
        'headers': dict(request.headers),
        'data': request.get_data(as_text=True)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True) 