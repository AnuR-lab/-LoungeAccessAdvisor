#!/bin/bash
set -e

echo "=== Stopping Streamlit Application ==="

# Stop the service if it's running
if systemctl is-active --quiet streamlit; then
    echo "Stopping Streamlit service..."
    systemctl stop streamlit
    echo "✅ Streamlit service stopped"
else
    echo "ℹ️  Streamlit service is not running"
fi

# Clean existing app directory to avoid file conflicts
echo "Cleaning app directory for fresh deployment..."
if [ -d "/home/ec2-user/app" ]; then
    cd /home/ec2-user
    rm -rf /home/ec2-user/app/*
    rm -rf /home/ec2-user/app/.venv
    rm -rf /home/ec2-user/app/.git
    rm -rf /home/ec2-user/app/.*
    echo "✅ App directory cleaned"
fi

# Recreate empty directory
mkdir -p /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app

echo "=== Stop Application Complete ==="