#!/bin/bash
# Test script for Claude.ai MCP connector integration

AZURE_URL="https://app-web-3ky2b33hy2dpm.azurewebsites.net"
API_KEY="YOUR_ANTHROPIC_API_KEY"

echo "Testing Telnyx MCP Server with Claude.ai MCP Connector"
echo "======================================================"
echo ""

# Get a fresh token
echo "1. Getting authentication token..."
TOKEN=$(python generate_azure_token.py)
echo "Token obtained: ${TOKEN:0:20}..."
echo ""

echo "2. Example Claude.ai API request with MCP connector:"
echo ""
cat << 'EOF'
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: mcp-client-2025-04-04" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1000,
    "messages": [{
      "role": "user", 
      "content": "List my Telnyx phone numbers and send a test SMS from one of them to +12486194535"
    }],
    "mcp_servers": [{
      "type": "url",
      "url": "https://app-web-3ky2b33hy2dpm.azurewebsites.net/mcp",
      "name": "telnyx",
      "authorization_token": "YOUR_JWT_TOKEN_HERE"
    }]
  }'
EOF

echo ""
echo "3. Replace the following in the request above:"
echo "   - YOUR_JWT_TOKEN_HERE with: $TOKEN"
echo "   - \$ANTHROPIC_API_KEY with your actual API key"
echo ""

echo "4. The MCP server provides access to these Telnyx tools:"
curl -s -X POST "$AZURE_URL/mcp" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  jq -r '.result.tools[].name' | head -10

echo "... and $(curl -s -X POST "$AZURE_URL/mcp" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  jq -r '.result.tools | length') more tools"

echo ""
echo "5. Server information:"
echo "   - Endpoint: $AZURE_URL/mcp"
echo "   - Transport: Streamable HTTP (supports both JSON and SSE)"
echo "   - Authentication: OAuth 2.0 Bearer token"
echo "   - Protocol: MCP 2024-11-05"