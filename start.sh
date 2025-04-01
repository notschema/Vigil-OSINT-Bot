#!/bin/bash
set -e

# Set default port values if not provided
API_PORT=${API_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-8080}

# Ensure directories exist
mkdir -p /app/logs /app/temp /app/config

# Check if maigret is installed, install if missing
echo "Checking if maigret is installed..."
python -c "import maigret" 2>/dev/null || {
    echo "Maigret not found, installing now..."
    pip install maigret
    echo "Maigret installation completed."
}

# Start the FastAPI backend in the background
cd /app
echo "Starting VigilBot API on port $API_PORT..."
uvicorn api.main:app --host 0.0.0.0 --port $API_PORT --log-level info &
API_PID=$!

# Wait for API to start
echo "Waiting for API to initialize..."
sleep 3

# Start Next.js frontend in the background - CORRECTED FOR STANDALONE MODE
cd /app/frontend
echo "Starting Next.js frontend on port $FRONTEND_PORT..."
# Check if we have the standalone server.js
if [ -f ".next/standalone/server.js" ]; then
    echo "Using standalone server mode..."
    # Set PORT for the standalone server
    export PORT=$FRONTEND_PORT
    node .next/standalone/server.js &
else
    echo "Standalone server not found, checking for alternatives..."
    # Try to run via node_modules as fallback
    if [ -f "node_modules/.bin/next" ]; then
        echo "Using node_modules/.bin/next as fallback..."
        NODE_OPTIONS='--inspect=0.0.0.0:9229' node_modules/.bin/next start -p $FRONTEND_PORT &
    else
        echo "ERROR: Could not find Next.js executable or standalone server"
        ls -la .next/ || echo "No .next directory"
    fi
fi
FRONTEND_PID=$!

# Function to handle termination
cleanup() {
    echo "Shutting down services..."
    kill -TERM $FRONTEND_PID 2>/dev/null
    kill -TERM $API_PID 2>/dev/null
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Keep the script running
echo "VigilBot interface is running!"
echo "API is available at http://localhost:$API_PORT"
echo "Frontend is available at http://localhost:$FRONTEND_PORT"
echo "NOTE: To access from other computers on your network, use your server IP address instead of localhost"
wait
