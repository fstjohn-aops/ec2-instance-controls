#!/usr/bin/env python3
"""
Simple Flask App
"""

from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Admin user IDs
ADMIN_USERS = {"U08QYU6AX0V"}

# User to EC2 instances mapping
USER_INSTANCES = {
    "U08QYU6AX0V": ["i-057cf7b437a182811"]
}

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/slack/test', methods=['POST'])
def slack_test():
    app.logger.info("=== SLACK REQUEST ===")
    app.logger.info(dict(request.form))
    app.logger.info("====================")
    
    return jsonify({
        'message': 'Slack data received',
        'headers': dict(request.headers),
        'data': request.get_data(as_text=True)
    })

@app.route('/admin/check', methods=['POST'])
def admin_check():
    user_id = request.form.get('user_id', '')
    user_name = request.form.get('user_name', 'Unknown')
    
    if user_id in ADMIN_USERS:
        return f"User: `{user_name}` is an administrator."
    else:
        return f"User: `{user_name}` is not an administrator."

@app.route('/ec2/power', methods=['POST'])
def set_ec2_power():
    user_id = request.form.get('user_id', '')
    text = request.form.get('text', '').strip()
    
    if user_id not in ADMIN_USERS:
        return "Only administrators can control EC2 instances."
    
    # Parse text: "i-057cf7b437a182811 on"
    parts = text.split()
    if len(parts) != 2:
        return "Usage: <instance-id> <on|off>"
    
    instance_id, power_state = parts
    
    if user_id not in USER_INSTANCES or instance_id not in USER_INSTANCES[user_id]:
        return "You don't have permission to control this instance."
    
    if power_state not in ['on', 'off']:
        return "Power state must be 'on' or 'off'."
    
    app.logger.info(f"AWS: Setting {instance_id} to {power_state}")
    return jsonify({
        'response_type': 'ephemeral',
        'text': f"Set `{instance_id}` to {power_state}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)