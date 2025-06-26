#!/bin/bash

export TESTING=1
source venv/bin/activate
# pip install -r requirements.txt
python3 test_app.py
