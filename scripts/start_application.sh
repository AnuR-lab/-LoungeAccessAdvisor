#!/bin/bash
set -e

echo "Starting Streamlit application..."

# Set PATH for UV
export PATH="/root/.cargo/bin:$PATH"

# Reload systemd
systemctl daemon-reload

# Enable and start the service
systemctl enable streamlit
systemctl start streamlit

# Wait for service to start
sleep 5

# Check if service is running
if systemctl is-active --quiet streamlit; then
    echo "✅ Streamlit application started successfully"
    systemctl status streamlit --no-pager
else
    echo "❌ Failed to start Streamlit application"
    journalctl -u streamlit -n 50 --no-pager
    exit 1
fi

echo "start_application completed successfully"