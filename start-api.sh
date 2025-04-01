#!/bin/bash
cd /app

# Create necessary directories with proper permissions
mkdir -p /app/logs /app/temp /app/config
chmod -R 777 /app/logs /app/temp /app/config

# Check for .env file
if [ ! -f "/app/.env" ]; then
    echo "WARNING: .env file not found at /app/.env"
    echo "Please ensure the .env file is mounted correctly"
    
    # Create a default .env file for testing
    echo "# Default .env file created by container
DISCORD_TOKEN=missing_token_please_mount_env_file
GITHUB_TOKEN=
" > /app/.env
    echo "Created a placeholder .env file for testing"
fi

# Display .env file (hide tokens)
echo "Checking .env file content:"
grep -v "TOKEN=" /app/.env || echo "No env vars found without TOKEN in name"

echo "Starting VigilBot API on port $API_PORT..."
# Start the API server in the background
uvicorn api.main:app --host 0.0.0.0 --port $API_PORT --log-level info &
API_PID=$!

# Wait for API to become available
echo "Waiting for API to initialize..."
MAX_RETRIES=30
RETRY_COUNT=0
API_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:$API_PORT/status > /dev/null; then
        echo "API is ready"
        API_READY=true
        break
    fi
    echo "API not ready yet, waiting... (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ "$API_READY" = true ]; then
    # Auto-start the bot using the API endpoint
    echo "Auto-starting the bot..."
    START_RESPONSE=$(curl -s -X POST http://localhost:$API_PORT/start)
    echo "Bot start response: $START_RESPONSE"
else
    echo "API did not start properly. Cannot start bot."
fi

# Print logs location
echo "Log files available in /app/logs directory"

# List running processes
echo "Checking running processes:"
ps aux | grep python | grep -v grep

# Keep the script running as long as the API is running
echo "API is running, monitoring status..."
while kill -0 $API_PID 2>/dev/null; do
    sleep 60
    # Check if the bot is still running through the API
    CURRENT_STATUS=$(curl -s http://localhost:$API_PORT/status | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo "Current bot status: $CURRENT_STATUS"
done

echo "API process has terminated. Exiting container."
