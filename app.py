#!/usr/bin/env python3
"""
Simple Flask App
"""

from flask import Flask, request
import logging
from src.handlers import handle_admin_check, handle_ec2_power, handle_list_instances

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/instances', methods=['POST'])
def list_instances():
    return handle_list_instances(request)

@app.route('/admin/check', methods=['POST'])
def admin_check():
    return handle_admin_check(request)

@app.route('/ec2/power', methods=['POST'])
def set_ec2_power():
    return handle_ec2_power(request)

@app.route('/ec2-power-state', methods=['POST'])
def ec2_power_state():
    return handle_ec2_power(request)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)