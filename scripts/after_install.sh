#!/bin/bash
set -e

echo "Running after_install script..."

cd /home/ec2-user/app

# Set PATH for UV
export PATH="/root/.cargo/bin:$PATH"

# Sync dependencies using UV
echo "Syncing dependencies with UV..."
uv sync --system

# Set correct permissions
chown -R ec2-user:ec2-user /home/ec2-user/app

echo "after_install completed successfully"