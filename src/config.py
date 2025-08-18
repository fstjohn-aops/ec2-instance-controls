import os
# AWS Configuration
AWS_REGION = 'us-west-2'
INSTANCE_NAME_SUFFIX = os.environ.get('INSTANCE_NAME_SUFFIX', 'aopstest.com')
# Schedule configuration
ON_TIME_LATEST_HOUR = int(os.environ.get('ON_TIME_LATEST_HOUR', 6))