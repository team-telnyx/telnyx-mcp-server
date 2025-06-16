# Remote MCP Server Deployment Guide

This guide explains how to deploy the Telnyx MCP Server as a remote server with OAuth authentication, suitable for use with Claude.ai's custom integrations.

## Overview

The Telnyx MCP Server now supports two deployment modes:
1. **Local Mode** (original) - Runs via stdio for Claude Desktop
2. **Remote Mode** (new) - Runs as an HTTP server with OAuth for Claude.ai

This guide covers the remote deployment option.

## Prerequisites

- Azure account with an active subscription
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) installed
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) installed
- Python 3.10+ installed locally for testing

## Architecture

The remote server includes:
- FastAPI web server with OAuth 2.0 authentication
- Azure AD integration for secure access
- JSON-RPC 2.0 MCP protocol over HTTP
- All existing Telnyx tools and capabilities
- Built-in test interface at `/test-auth`

## Quick Start

### 1. Create Azure AD App Registration

```bash
# Login to Azure
az login

# Create app registration
az ad app create --display-name "telnyx-mcp-server-$USER" \
  --sign-in-audience AzureADMyOrg \
  --web-redirect-uris "http://localhost:8000/auth/callback"

# Get the app ID
APP_ID=$(az ad app list --display-name "telnyx-mcp-server-$USER" --query "[0].appId" -o tsv)
echo "Your App ID: $APP_ID"

# Create a client secret
CLIENT_SECRET=$(az ad app credential reset --id $APP_ID --query "password" -o tsv)
echo "Your Client Secret: $CLIENT_SECRET"

# Get your tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Your Tenant ID: $TENANT_ID"
```

Save these values - you'll need them for configuration.

### 2. Local Testing

1. **Clone and setup**:
   ```bash
   git clone https://github.com/team-telnyx/telnyx-mcp-server.git
   cd telnyx-mcp-server
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values from step 1
   ```

3. **Run the server**:
   ```bash
   uvicorn telnyx_mcp_server.remote.server:app --reload --port 8000
   ```

4. **Test authentication**:
   - Open http://localhost:8000/test-auth
   - Click "Start Azure OAuth Login"
   - Complete the login flow
   - Copy your JWT token

5. **Test MCP endpoints**:
   - Use the test interface to verify tools are working
   - Or use curl with your token:
   ```bash
   curl -X POST http://localhost:8000/mcp/stream \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
   ```

### 3. Deploy to Azure

1. **Initialize azd**:
   ```bash
   azd auth login
   azd init
   # Choose a name for your environment (e.g., "prod")
   ```

2. **Set configuration**:
   ```bash
   # OAuth settings
   azd env set AZURE_CLIENT_ID "$APP_ID"
   azd env set AZURE_CLIENT_SECRET "$CLIENT_SECRET"
   azd env set AZURE_TENANT_ID "$TENANT_ID"
   
   # Generate a secure JWT secret
   azd env set JWT_SECRET_KEY "$(openssl rand -base64 32)"
   
   # Set your Telnyx API key
   azd env set TELNYX_API_KEY "your-telnyx-api-key"
   ```

3. **Deploy**:
   ```bash
   azd up
   ```

4. **Update redirect URI**:
   After deployment, update your app registration with the production URL:
   ```bash
   # Get your deployed URL
   APP_URL=$(azd env get-values | grep WEB_URI | cut -d'"' -f4)
   
   # Add production redirect URI
   az ad app update --id $APP_ID --web-redirect-uris \
     "http://localhost:8000/auth/callback" \
     "$APP_URL/auth/callback"
   ```

### 4. Configure in Claude.ai

1. Go to Claude.ai Settings → Integrations
2. Click "Add custom integration"
3. Enter your server URL (from `azd env get-values`)
4. Claude will detect the OAuth configuration automatically
5. Complete the authentication flow
6. Enable the Telnyx tools you want to use

## Testing Your Deployment

### Health Check
```bash
curl https://your-app.azurewebsites.net/health
```

### Authentication Test
Visit: `https://your-app.azurewebsites.net/test-auth`

### MCP Capabilities
```bash
curl https://your-app.azurewebsites.net/mcp/capabilities
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_CLIENT_ID` | Azure AD App Registration Client ID | Yes |
| `AZURE_CLIENT_SECRET` | Azure AD App Registration Secret | Yes |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Yes |
| `AZURE_REDIRECT_URI` | OAuth callback URL | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes |
| `TELNYX_API_KEY` | Your Telnyx API key | Yes |
| `JWT_EXPIRATION_HOURS` | Token expiration time (default: 24) | No |

## Security Considerations

1. **Authentication**: All MCP endpoints require valid JWT tokens
2. **HTTPS**: Azure App Service enforces HTTPS for all traffic
3. **Secrets**: All sensitive values are stored as app settings (consider using Key Vault for production)
4. **CORS**: Configure allowed origins appropriately for production
5. **Token Expiration**: Tokens expire after 24 hours by default

## Troubleshooting

### Authentication Issues
- Verify redirect URIs match exactly (including trailing slashes)
- Check Azure AD app permissions
- Ensure client secret hasn't expired

### Deployment Issues
- Check Application Insights for detailed logs
- Verify all environment variables are set correctly
- Use `azd monitor` to stream logs

### MCP Connection Issues
- Verify authentication token is valid
- Check CORS configuration
- Test with the built-in test interface first

## Advanced Configuration

### Custom Domain
```bash
az webapp config hostname add --webapp-name YOUR_APP_NAME \
  --resource-group YOUR_RG --hostname your-domain.com
```

### Scaling
Update the App Service Plan in `infra/core/host/appserviceplan.bicep`:
```bicep
sku: {
  name: 'P1v3'  // Premium tier for production
  capacity: 2    // Number of instances
}
```

### Key Vault Integration
For production, consider storing secrets in Azure Key Vault. Update `infra/app/web.bicep` to reference Key Vault secrets instead of plain text values.

## Monitoring

- **Application Insights**: Automatically configured for monitoring
- **Log Streaming**: `az webapp log tail --name YOUR_APP_NAME --resource-group YOUR_RG`
- **Metrics**: Available in Azure Portal under your App Service

## Support

For issues specific to:
- **Remote deployment**: Open an issue with the `remote-mcp` label
- **OAuth/Authentication**: Check Azure AD logs first
- **Telnyx API**: Refer to Telnyx documentation

## Next Steps

1. Test all Telnyx tools with authentication
2. Configure production-appropriate CORS settings
3. Set up monitoring alerts
4. Consider implementing rate limiting
5. Plan for token refresh strategy