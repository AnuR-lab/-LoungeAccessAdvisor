#!/bin/bash
set -e

echo "Stopping Streamlit application..."

# Stop the service if it's running
if systemctl is-active --quiet streamlit; then
    systemctl stop streamlit
    echo "Streamlit service stopped"
else
    echo "Streamlit service is not running"
fi

echo "stop_application completed successfully"