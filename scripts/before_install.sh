#!/bin/bash
set -e

echo "=== Before Install Script ==="

# Clean existing app directory to avoid file conflicts
if [ -d "/home/ec2-user/app" ]; then
    echo "Cleaning existing app directory..."
    rm -rf /home/ec2-user/app/*
    rm -rf /home/ec2-user/app/.venv
    rm -rf /home/ec2-user/app/.git
    echo "✅ Directory cleaned"
fi

# Ensure UV is installed for ec2-user
if ! su - ec2-user -c 'command -v uv' &> /dev/null; then
    echo "Installing UV for ec2-user..."
    su - ec2-user -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    echo "✅ UV installed"
else
    echo "✅ UV already installed"
fi

# Ensure git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    yum install -y git
    echo "✅ Git installed"
else
    echo "✅ Git already installed"
fi

# Ensure app directory exists
mkdir -p /home/ec2-user/app
chown -R ec2-user:ec2-user /home/ec2-user/app

echo "=== Before Install Complete ==="