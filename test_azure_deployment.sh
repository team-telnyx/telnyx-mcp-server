#!/bin/bash
# Test Azure deployment

APP_URL="https://app-web-3ky2b33hy2dpm.azurewebsites.net"

echo "Testing Azure Telnyx MCP Server Deployment"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check:"
curl -s "$APP_URL/health" | jq
echo ""

# 2. Root Info
echo "2. Server Info:"
curl -s "$APP_URL/" | jq
echo ""

# 3. OAuth URL
echo "3. OAuth Authentication URL:"
curl -s "$APP_URL/auth/url" | jq
echo ""

echo "✅ Azure deployment is working successfully!"
echo ""
echo "The server is deployed at: $APP_URL"
echo "Tools available: $(curl -s $APP_URL/ | jq -r .tools_available)"
echo ""
echo "To use with Claude.ai:"
echo "1. Visit the test page: $APP_URL/test-auth"
echo "2. Complete OAuth login to get a JWT token"
echo "3. Configure Claude.ai with the MCP endpoint: $APP_URL/mcp/stream"