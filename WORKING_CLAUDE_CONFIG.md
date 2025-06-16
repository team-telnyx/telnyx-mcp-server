# Working Configuration for Claude.ai MCP Connector

## Summary

The Telnyx Remote MCP Server is successfully deployed and working at:
- **URL**: https://app-web-3ky2b33hy2dpm.azurewebsites.net/mcp
- **Transport**: Streamable HTTP (supports both JSON and SSE)
- **Authentication**: JWT Bearer token
- **Tools Available**: 46 Telnyx tools

## Test Results

1. **Local Testing**: ✅ All tests passing
   - JSON responses working
   - SSE responses working
   - Error handling working

2. **Azure Deployment**: ✅ Deployed and responding
   - Health check: Working
   - Initialize method: Working
   - Tools list: Returns 46 tools
   - Both JSON and SSE formats: Working

3. **Claude.ai Integration**: ⚠️ "Connection closed" error
   - This might be due to:
     - Token expiration (tokens expire after 24 hours)
     - Claude expecting a different SSE format
     - Need for persistent connection handling

## Configuration for Claude.ai

```json
{
  "mcp_servers": [
    {
      "type": "url",
      "url": "https://app-web-3ky2b33hy2dpm.azurewebsites.net/mcp",
      "name": "telnyx",
      "authorization_token": "YOUR_JWT_TOKEN_HERE"
    }
  ]
}
```

## Getting a Fresh Token

1. Visit: https://app-web-3ky2b33hy2dpm.azurewebsites.net/test-auth
2. Click "Start Azure OAuth Login"
3. Complete Microsoft authentication
4. Copy the JWT token from the success page

## Available Tools

The server provides 46 Telnyx tools including:
- Messaging: send_message, get_message
- Phone Numbers: list_phone_numbers, get_phone_number, update_phone_number
- Call Control: make_call, hangup, speak, transfer
- AI Assistants: create_assistant, chat_with_assistant
- Cloud Storage: upload_file, download_file, list_objects
- And many more...

## Troubleshooting

If you get "Connection closed" error:
1. Ensure your token is fresh (not expired)
2. Try using the token in a direct API call first to verify it works
3. Check if Claude is sending the correct Accept headers

## Next Steps

The server implementation follows the MCP Streamable HTTP specification correctly. The "Connection closed" error from Claude might require:
1. Investigating Claude's specific requirements for SSE connections
2. Adding session management support
3. Implementing keep-alive mechanisms for SSE streams