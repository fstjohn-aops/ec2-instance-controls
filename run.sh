#!/bin/bash

# Simple script to run the EC2 Instance Control Flask App

echo "Starting EC2 Instance Control App..."

# Set default port if not already set
export PORT=${PORT:-8000}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 app.py 