#!/usr/bin/env python3
"""
Simple Flask App
"""

from flask import Flask, request
import logging
import json
from datetime import datetime, timezone
from src.handlers import handle_ec2_power, handle_list_instances, handle_ec2_schedule
import os

app = Flask(__name__)

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    def format(self, record):
        # If the message is already a JSON string, parse it
        if record.getMessage().startswith('AUDIT:') or record.getMessage().startswith('AWS_AUDIT:') or record.getMessage().startswith('SCHEDULE_AUDIT:') or record.getMessage().startswith('REQUEST_AUDIT:'):
            # Extract the JSON part after the prefix
            prefix, json_str = record.getMessage().split(' ', 1)
            try:
                # Parse the JSON and add standard fields
                log_data = json.loads(json_str)
                log_data['level'] = record.levelname
                log_data['logger'] = record.name
                return json.dumps(log_data)
            except json.JSONDecodeError:
                # Fall back to regular formatting if JSON parsing fails
                pass
        
        # Regular log message formatting
        return super().format(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Apply structured formatter to root logger
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(StructuredFormatter())

logger = logging.getLogger(__name__)

def _log_request():
    """Log incoming requests for auditing purposes"""
    timestamp = datetime.now(timezone.utc).isoformat()
    user_id = request.form.get('user_id', 'unknown')
    user_name = request.form.get('user_name', 'unknown')
    
    log_entry = {
        'timestamp': timestamp,
        'method': request.method,
        'endpoint': request.endpoint,
        'user_id': user_id,
        'user_name': user_name,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'pod_name': os.environ.get('HOSTNAME', 'unknown'),
        'namespace': os.environ.get('POD_NAMESPACE', 'unknown'),
        'deployment': os.environ.get('DEPLOYMENT_NAME', 'unknown')
    }
    
    # Log form data for POST requests (excluding sensitive data)
    if request.method == 'POST' and request.form:
        form_data = dict(request.form)
        # Remove potentially sensitive data
        if 'text' in form_data:
            form_data['text'] = form_data['text'][:100] + '...' if len(form_data['text']) > 100 else form_data['text']
        log_entry['form_data'] = form_data
    
    logging.info(f"REQUEST_AUDIT: {json.dumps(log_entry)}")

@app.before_request
def before_request():
    """Log all incoming requests"""
    _log_request()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        'status': 'healthy',
        'timestamp': timestamp,
        'service': 'ec2-instance-controls'
    }

@app.route('/instances', methods=['POST'])
def list_instances():
    return handle_list_instances(request)

@app.route('/ec2/power', methods=['POST'])
def set_ec2_power():
    return handle_ec2_power(request)

@app.route('/ec2-power-state', methods=['POST'])
def ec2_power_state():
    return handle_ec2_power(request)

@app.route('/ec2-schedule', methods=['POST'])
def ec2_schedule():
    return handle_ec2_schedule(request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)