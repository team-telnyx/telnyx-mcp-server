#!/bin/bash
# Script to run Telnyx Remote MCP Server locally

echo "Starting Telnyx Remote MCP Server..."
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "⚠️  Please edit .env and add your configuration values!"
        exit 1
    else
        echo "❌ No .env.example file found!"
        exit 1
    fi
fi

# Check for required environment variables
if ! grep -q "AZURE_CLIENT_ID=.*[^=]" .env; then
    echo "⚠️  Warning: AZURE_CLIENT_ID not configured in .env"
    echo "   OAuth authentication will not work without Azure AD configuration."
    echo "   See REMOTE_DEPLOYMENT.md for setup instructions."
fi

if ! grep -q "TELNYX_API_KEY=.*[^=]" .env; then
    echo "⚠️  Warning: TELNYX_API_KEY not configured in .env"
    echo "   Telnyx tools will not work without an API key."
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Test authentication at: http://localhost:8000/test-auth"
echo "API documentation at: http://localhost:8000/docs"
echo ""

# Set Python path
export PYTHONPATH="${PYTHONPATH}:./src"

# Run the server
uvicorn telnyx_mcp_server.remote.server:app --reload --host 0.0.0.0 --port 8000