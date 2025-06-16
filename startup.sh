#!/bin/bash
# Startup script for Telnyx Remote MCP Server on Azure App Service

echo "Starting Telnyx Remote MCP Server..."
echo "===================================="

export PYTHONUNBUFFERED=1

# Log environment info
echo "Python version: $(python --version)"
echo "Server module: src.telnyx_mcp_server.remote.server:app"
echo "Port: 8000"
echo ""

# Function to check health endpoint
check_health() {
    curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null
}

# Start the application with gunicorn
echo "Starting gunicorn with uvicorn workers..."
gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --timeout 600 \
  --chdir src \
  --access-logfile '-' \
  --error-logfile '-' \
  --log-level debug \
  telnyx_mcp_server.remote.server:app &

# Store PID
GUNICORN_PID=$!

# Wait for server to be healthy
echo "Waiting for server to be ready..."
for i in {1..30}; do
    sleep 2
    if [ "$(check_health)" = "200" ]; then
        echo "✓ Server is healthy and ready to accept requests"
        echo "Health check passed at: $(date)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ Warning: Health check did not pass after 60 seconds"
    fi
done

# Keep the process in foreground
wait $GUNICORN_PID