# Server Management Guide

This guide covers how to manage the Telnyx MCP Server in different environments.

## Quick Start

### Development Server (with hot reload)
```bash
# Start development server
./dev_server.sh start

# View logs
./dev_server.sh logs

# Restart server
./dev_server.sh restart

# Stop server
./dev_server.sh stop
```

### Production Server
```bash
# Start production server
./server_manager.sh start

# Check status
./server_manager.sh status

# View logs
./server_manager.sh logs

# Stop server
./server_manager.sh stop
```

## Server Management Scripts

### `dev_server.sh` - Development Server Manager

Perfect for local development with automatic reload on code changes.

**Features:**
- Hot reload enabled (automatically restarts on code changes)
- Detailed error messages and logging
- Color-coded log output
- Easy access to test endpoints

**Commands:**
- `start` - Start the development server with hot reload
- `stop` - Stop the development server
- `restart` - Restart the development server
- `status` - Show server status
- `logs` - Follow server logs with color highlighting
- `errors` - Show recent errors from logs

**Example:**
```bash
# Start development server
./dev_server.sh start

# Server will be available at:
# - http://localhost:8000 (API)
# - http://localhost:8000/docs (API Documentation)
# - http://localhost:8000/test-auth (OAuth Test Page)
```

### `server_manager.sh` - Production Server Manager

For running the server in production or staging environments.

**Features:**
- Stable server process management
- PID file tracking
- Graceful shutdown with fallback to force kill
- Process cleanup utilities

**Commands:**
- `start` - Start the server
- `stop` - Stop the server (graceful shutdown)
- `restart` - Restart the server
- `status` - Show server status
- `logs` - Show recent log entries
- `cleanup` - Kill all server processes (use with caution)

**Example:**
```bash
# Start production server
./server_manager.sh start

# Check if running
./server_manager.sh status
✓ Server is running (PID: 12345)
  URL: http://localhost:8000
  Module: src.telnyx_mcp_server.remote.server
  Log file: server.log
```

## Systemd Service (Linux Production)

For production Linux servers, use the systemd service for automatic startup and management.

### Installation

1. Copy the service file:
```bash
sudo cp telnyx-mcp-server.service /etc/systemd/system/
```

2. Create application directory:
```bash
sudo mkdir -p /opt/telnyx-mcp-server
sudo cp -r . /opt/telnyx-mcp-server/
sudo chown -R www-data:www-data /opt/telnyx-mcp-server
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telnyx-mcp-server
sudo systemctl start telnyx-mcp-server
```

### Management Commands

```bash
# Start the service
sudo systemctl start telnyx-mcp-server

# Stop the service
sudo systemctl stop telnyx-mcp-server

# Restart the service
sudo systemctl restart telnyx-mcp-server

# Check status
sudo systemctl status telnyx-mcp-server

# View logs
sudo journalctl -u telnyx-mcp-server -f

# View recent logs
sudo journalctl -u telnyx-mcp-server -n 100
```

## Azure App Service Deployment

For Azure deployments, the server starts automatically using the `startup.sh` script.

### Manual Control (via SSH)

```bash
# SSH into the App Service
az webapp ssh --name <app-name> --resource-group <resource-group>

# Restart the application
supervisorctl restart gunicorn

# View logs
tail -f /home/LogFiles/application.log
```

## Environment Variables

Make sure these are set before starting the server:

```bash
# Required
export TELNYX_API_KEY="your-api-key"
export JWT_SECRET_KEY="your-secret-key"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_TENANT_ID="your-tenant-id"

# Optional
export JWT_EXPIRATION_HOURS="24"
export LOG_LEVEL="INFO"
```

## Troubleshooting

### Server won't start

1. Check if port 8000 is already in use:
```bash
lsof -i :8000
```

2. Clean up stray processes:
```bash
./server_manager.sh cleanup
```

3. Check logs for errors:
```bash
./server_manager.sh logs
# or for development
./dev_server.sh errors
```

### Server stops unexpectedly

1. Check system resources:
```bash
free -h
df -h
```

2. Check Python dependencies:
```bash
pip install -r requirements.txt
```

3. Check environment variables:
```bash
env | grep TELNYX
env | grep AZURE
```

### OAuth issues

1. Verify OAuth endpoints are accessible:
```bash
curl http://localhost:8000/.well-known/oauth-protected-resource
curl http://localhost:8000/.well-known/oauth-authorization-server
```

2. Test OAuth flow:
```bash
# Open in browser
http://localhost:8000/test-auth
```

## Best Practices

1. **Development**: Always use `dev_server.sh` for local development
2. **Production**: Use systemd service or cloud-native deployment
3. **Monitoring**: Set up log aggregation and monitoring
4. **Security**: Keep environment variables secure
5. **Updates**: Test thoroughly before deploying to production

## Log Files

- Development: `server_dev.log`
- Production: `server.log`
- Systemd: `journalctl -u telnyx-mcp-server`
- Azure: `/home/LogFiles/application.log`