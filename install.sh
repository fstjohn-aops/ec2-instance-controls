#!/bin/bash

# Update system packages
sudo yum update -y

# Install required packages
sudo yum install -y python3 python3-pip nginx git

# Install Python dependencies
pip3 install -r requirements.txt

# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/nginx.conf

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Make scripts executable
chmod +x run.sh test.sh

echo "Installation complete!"
echo "Run the application with: ./run.sh"
echo "Test the application with: ./test.sh" 