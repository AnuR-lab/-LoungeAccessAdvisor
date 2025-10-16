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

echo "=== Stop Application Complete ==="