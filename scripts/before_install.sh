#!/bin/bash
set -e

echo "Running before_install script..."

# Ensure UV is installed
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.cargo/bin:$PATH"
fi

# Create app directory if it doesn't exist
mkdir -p /home/ec2-user/app

echo "before_install completed successfully"