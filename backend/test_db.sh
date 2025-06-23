#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Testing database creation..."

# Test if we can create the database file
python3 -c "
import sqlite3
import os

try:
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Create database
    db_path = 'data/ec2_instances.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
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
    
    # Insert test data
    cursor.execute('''
        INSERT OR REPLACE INTO instance_users 
        (instance_id, instance_name, slack_user_id, slack_username)
        VALUES (?, ?, ?, ?)
    ''', ('i-test-1', 'Test Instance', 'U123', 'testuser'))
    
    conn.commit()
    conn.close()
    
    print('Database created successfully!')
    print(f'Database file: {db_path}')
    
    # Check file exists
    if os.path.exists(db_path):
        print('✅ Database file exists')
        print(f'File size: {os.path.getsize(db_path)} bytes')
    else:
        print('❌ Database file not found')
        
except Exception as e:
    print(f'❌ Error: {e}')
"

echo "Test completed." 