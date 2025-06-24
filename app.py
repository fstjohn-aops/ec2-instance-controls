#!/usr/bin/env python3
"""
Simple EC2 Instance Control Flask App
A minimal Flask application for managing EC2 instances via REST API
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = int(os.environ.get('PORT', 8000))
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'
DB_PATH = os.environ.get('DB_PATH', 'instances.db')

# Mock data for test mode
MOCK_INSTANCES = {
    'i-test-1': {'state': 'running', 'name': 'Test Instance 1'},
    'i-test-2': {'state': 'stopped', 'name': 'Test Instance 2'},
    'i-test-3': {'state': 'running', 'name': 'Test Instance 3'}
}

def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instance_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT UNIQUE NOT NULL,
                instance_name TEXT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

# Initialize database on startup
init_db()

def get_instance_status(instance_id: str) -> Optional[str]:
    """Get instance status (mock implementation)"""
    if TEST_MODE:
        return MOCK_INSTANCES.get(instance_id, {}).get('state')
    
    # In real implementation, you would use boto3 here
    # For simplicity, we'll just return a mock status
    logger.info(f"Getting status for instance {instance_id}")
    return 'running'  # Mock response

def start_instance(instance_id: str) -> str:
    """Start an EC2 instance (mock implementation)"""
    if TEST_MODE:
        if instance_id in MOCK_INSTANCES:
            MOCK_INSTANCES[instance_id]['state'] = 'running'
            logger.info(f"TEST MODE: Started instance {instance_id}")
            return 'running'
        return 'unknown'
    
    # In real implementation, you would use boto3 here
    logger.info(f"Starting instance {instance_id}")
    return 'running'  # Mock response

def stop_instance(instance_id: str) -> str:
    """Stop an EC2 instance (mock implementation)"""
    if TEST_MODE:
        if instance_id in MOCK_INSTANCES:
            MOCK_INSTANCES[instance_id]['state'] = 'stopped'
            logger.info(f"TEST MODE: Stopped instance {instance_id}")
            return 'stopped'
        return 'unknown'
    
    # In real implementation, you would use boto3 here
    logger.info(f"Stopping instance {instance_id}")
    return 'stopped'  # Mock response

# API Routes

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'test_mode': TEST_MODE
    })

@app.route('/api/instances', methods=['GET'])
def list_instances():
    """List all instances"""
    if TEST_MODE:
        instances = [
            {'id': instance_id, 'name': data['name'], 'state': data['state']}
            for instance_id, data in MOCK_INSTANCES.items()
        ]
    else:
        # Mock response for non-test mode
        instances = [
            {'id': 'i-1234567890abcdef0', 'name': 'Production Server', 'state': 'running'},
            {'id': 'i-0987654321fedcba0', 'name': 'Staging Server', 'state': 'stopped'}
        ]
    
    return jsonify({'instances': instances})

@app.route('/api/instances/<instance_id>/status', methods=['GET'])
def get_instance_status_api(instance_id):
    """Get status of a specific instance"""
    status = get_instance_status(instance_id)
    if status is None:
        return jsonify({'error': 'Instance not found'}), 404
    
    return jsonify({
        'instance_id': instance_id,
        'status': status
    })

@app.route('/api/instances/<instance_id>/start', methods=['POST'])
def start_instance_api(instance_id):
    """Start a specific instance"""
    try:
        new_status = start_instance(instance_id)
        return jsonify({
            'instance_id': instance_id,
            'status': new_status,
            'message': f'Instance {instance_id} started successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instances/<instance_id>/stop', methods=['POST'])
def stop_instance_api(instance_id):
    """Stop a specific instance"""
    try:
        new_status = stop_instance(instance_id)
        return jsonify({
            'instance_id': instance_id,
            'status': new_status,
            'message': f'Instance {instance_id} stopped successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assignments', methods=['GET'])
def list_assignments():
    """List all instance-user assignments"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT instance_id, instance_name, user_id, username, created_at
            FROM instance_users
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        assignments = [
            {
                'instance_id': row[0],
                'instance_name': row[1],
                'user_id': row[2],
                'username': row[3],
                'created_at': row[4]
            }
            for row in rows
        ]
        
        return jsonify({'assignments': assignments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assignments', methods=['POST'])
def create_assignment():
    """Create a new instance-user assignment"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['instance_id', 'user_id', 'username']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO instance_users 
            (instance_id, instance_name, user_id, username)
            VALUES (?, ?, ?, ?)
        ''', (
            data['instance_id'],
            data.get('instance_name', ''),
            data['user_id'],
            data['username']
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Assignment created for instance {data["instance_id"]}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assignments/<user_id>', methods=['DELETE'])
def delete_assignment(user_id):
    """Delete an instance-user assignment"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM instance_users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Assignment deleted for user {user_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting EC2 Instance Control App on port {PORT}")
    logger.info(f"Test mode: {TEST_MODE}")
    app.run(host='0.0.0.0', port=PORT, debug=False) 