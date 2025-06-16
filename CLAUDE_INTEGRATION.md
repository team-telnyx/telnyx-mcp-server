# Telnyx MCP Server - Claude.ai Integration Guide

This guide explains how to integrate the Telnyx Remote MCP Server with Claude.ai using the MCP connector feature.

## Prerequisites

1. Your Telnyx MCP server must be deployed and accessible via HTTPS
2. You need a valid JWT token from the authentication flow
3. You need Claude.ai access with MCP connector support

## Getting Your JWT Token

1. Visit your deployed server's test page: `https://YOUR-APP.azurewebsites.net/test-auth`
2. Click "Start Azure OAuth Login"
3. Complete the Microsoft login
4. Copy the JWT token displayed on the success page

## Configuring Claude.ai

**Important**: Claude.ai does NOT handle OAuth flows automatically. You must obtain a JWT token first and provide it in the configuration.

When using Claude.ai with the MCP connector feature, you'll need to provide the following configuration:

```json
{
  "mcp_servers": [
    {
      "type": "url",
      "url": "https://YOUR-APP.azurewebsites.net/mcp/stream",
      "name": "telnyx",
      "authorization_token": "Bearer YOUR_JWT_TOKEN_HERE"
    }
  ]
}
```

**Note**: 
- Use `/mcp/stream` endpoint (not `/mcp`)
- Include "Bearer " prefix with your token
- Token must be obtained manually via the test page

Replace:
- `YOUR-APP` with your actual Azure app name (e.g., `app-web-3ky2b33hy2dpm`)
- `YOUR_JWT_TOKEN_HERE` with the JWT token you obtained from the authentication flow

## Required Headers

When making requests to Claude.ai API with MCP connector:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: mcp-client-2025-04-04" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "List available Telnyx tools"}],
    "mcp_servers": [{
      "type": "url",
      "url": "https://YOUR-APP.azurewebsites.net/mcp",
      "name": "telnyx",
      "authorization_token": "YOUR_JWT_TOKEN"
    }]
  }'
```

## Available Tools

Once connected, Claude will have access to all 46 Telnyx tools including:

- **Messaging**: send_message, get_message
- **Phone Numbers**: list_phone_numbers, get_phone_number, update_phone_number
- **Call Control**: create_call, answer_call, hangup_call
- **AI**: create_assistant, chat_with_assistant
- **Storage**: upload_file, download_file, list_files
- And many more...

## Token Expiration

JWT tokens expire after 24 hours by default. When your token expires:

1. Return to the test page
2. Complete the OAuth flow again
3. Update your Claude.ai configuration with the new token

## Troubleshooting

### "Invalid token" error
- Ensure you're using the correct JWT token
- Check if the token has expired (24 hours)
- Verify the token includes "Bearer " prefix if required

### "Failed to discover OAuth metadata" error
- This is expected - Claude.ai looks for OAuth metadata but we use pre-obtained tokens
- Simply provide your JWT token in the configuration as shown above

### "Method not found" error
- Ensure you're using the `/mcp/stream` endpoint
- Verify the server is running and accessible

### No tools showing up
- Check the server logs for initialization errors
- Ensure the TELNYX_API_KEY is properly configured in Azure
- Verify the server started successfully with all 46 tools

## Security Notes

- JWT tokens are sensitive - treat them like passwords
- Don't share tokens publicly or commit them to repositories
- Use Azure Key Vault for production deployments
- Consider implementing token refresh for long-running sessions