#!/usr/bin/env python3
"""
Simple Flask App
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/slack/test', methods=['POST'])
def slack_test():
    return jsonify({
        'message': 'Slack data received',
        'headers': dict(request.headers),
        'data': request.get_data(as_text=True)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 