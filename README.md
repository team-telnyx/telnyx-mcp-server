# Telnyx Local Model Context Protocol (MCP) Server

> **⚠️ DEPRECATED**: This Python-based MCP server is deprecated. Please migrate to the official TypeScript version:
>
> **New Repository:** https://github.com/team-telnyx/telnyx-node/tree/master/packages/mcp-server

---

Official Telnyx Local Model Context Protocol (MCP) Server that enables interaction with powerful telephony, messaging, and AI assistant APIs. This server allows MCP clients like Claude Desktop, Cursor, Windsurf, OpenAI Agents and others to manage phone numbers, send messages, make calls, and create AI assistants.

## Quickstart with Claude Desktop

1. Get your API key from the [Telnyx Portal](https://portal.telnyx.com/#/api-key).
2. Install `uvx` (Python package manager), install with `curl -LsSf https://astral.sh/uv/install.sh | sh` , `brew install uv` or see the `uv` repo for additional install methods.
3. Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```json
{
  "mcpServers": {
    "Telnyx": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/team-telnyx/telnyx-mcp-server.git", "telnyx-mcp-server"],
      "env": {
        "TELNYX_API_KEY": "<insert-your-api-key-here>"
      }
    }
  }
}
```

If you're using Windows, you will have to enable "Developer Mode" in Claude Desktop to use the MCP server. Click "Help" in the hamburger menu at the top left and select "Enable Developer Mode".

## Running After Download

1. Get your API key from the [Telnyx Portal](https://portal.telnyx.com/#/api-key).

2. Install `uvx` (Python package manager), install with `curl -LsSf https://astral.sh/uv/install.sh | sh` , `brew install uv` or see the `uv` repo for additional install methods.

3. **Clone the Git Repository**  
   Use Git to download the Telnyx MCP Server locally:
   ```bash
   git clone https://github.com/team-telnyx/telnyx-mcp-server.git
   cd telnyx-mcp-server
   ```

4. **Configure and Run with uvx**  
   In your Claude config, you can reference the local folder by using the `--from` argument. For example:
   ```json
   {
     "mcpServers": {
       "Telnyx": {
         "command": "uvx",
         "args": ["--from", "/path/to/telnyx-mcp-server", "telnyx-mcp-server"],
         "env": {
           "TELNYX_API_KEY": "<insert-your-api-key-here>"
         }
       }
     }
   }
   ```

5. This instructs Claude to run the server from the folder you cloned. 
Replace “/path/to/telnyx-mcp-server” with the actual location of the repository.

## Available Tools

### Assistant Tools
- Create AI assistants with custom instructions and configurations
- List existing assistants
- Get assistant details
- Update assistant properties
- Delete assistants
- Get assistant TEXML configurations

### Call Control Tools
- Make outbound phone calls
- Hang up active calls
- Transfer calls to new destinations
- Play audio files during calls
- Stop audio playback
- Send DTMF tones
- Speak text using text-to-speech

### Messaging Tools
- Send SMS and MMS messages
- Get message details
- Access and view ongoing SMS conversations (`resource://sms/conversations`)

### Phone Number Tools
- List your phone numbers
- Buy new phone numbers
- Update phone number configurations
- List available phone numbers

### Connection Tools
- List voice connections
- Get connection details
- Update connection configurations

### Cloud Storage Tools
- Create buckets compatible with Telnyx Cloud Storage
- List buckets across all regions
- Upload files
- Download files
- List objects in a bucket
- Delete objects
- Get bucket location information

### Embeddings Tools
- List existing embedded buckets
- Scrape and embed a website URL
- Create embeddings for your own files

### Secrets Manager Tools
- List integration secrets
- Create new bearer or basic secrets
- Delete integration secrets

## Tool Filtering

You can selectively enable or disable specific tools when running the MCP server. This is useful when you only need a subset of the available functionality.

### Listing Available Tools

To see all available tools:

```bash
uvx --from /path/to/telnyx-mcp-server telnyx-mcp-server --list-tools
```

### Enabling Specific Tools

You can enable only specific tools using either:

1. **Command-line argument**:
   ```bash
   uvx --from /path/to/telnyx-mcp-server telnyx-mcp-server --tools "send_message,get_message,list_phone_numbers"
   ```

2. **Environment variable**:
   ```json
   {
     "mcpServers": {
       "Telnyx": {
         "command": "uvx",
         "args": ["--from", "/path/to/telnyx-mcp-server", "telnyx-mcp-server"],
         "env": {
           "TELNYX_API_KEY": "<insert-your-api-key-here>",
           "TELNYX_MCP_TOOLS": "send_message,get_message,list_phone_numbers"
         }
       }
     }
   }
   ```

### Excluding Specific Tools

You can exclude specific tools while enabling all others:

1. **Command-line argument**:
   ```bash
   uvx --from /path/to/telnyx-mcp-server telnyx-mcp-server --exclude-tools "make_call,send_dtmf"
   ```

2. **Environment variable**:
   ```json
   {
     "mcpServers": {
       "Telnyx": {
         "command": "uvx",
         "args": ["--from", "/path/to/telnyx-mcp-server", "telnyx-mcp-server"],
         "env": {
           "TELNYX_API_KEY": "<insert-your-api-key-here>",
           "TELNYX_MCP_EXCLUDE_TOOLS": "make_call,send_dtmf"
         }
       }
     }
   }
   ```

## Example Usage

Try asking Claude:

* "Create an AI agent that can handle customer service for an e-commerce business"
* "Send a text message to +5555551234 saying 'Your appointment is confirmed for tomorrow at 3pm'"
* "Make a call to my customer at +5555551234 and transfer them to my support team"
* "Find me a phone number in Chicago with area code 312"
* "Create an auto-attendant system using Telnyx AI assistants and voice features"

## Webhook Receiver

The MCP server includes a webhook receiver that can handle Telnyx webhooks directly through ngrok. This is useful for receiving call events and other notifications from Telnyx.

### Enabling Webhooks

To enable the webhook receiver, you can either use the `--webhook-enabled` command-line flag or set the `WEBHOOK_ENABLED=true` environment variable. If an `NGROK_AUTHTOKEN` is also provided (see 'Ngrok Integration' below), the ngrok tunnel will be automatically attempted when the server starts. The command-line flag takes precedence if both are set.

**Using Command-Line Flag:**

```bash
telnyx-mcp-server --webhook-enabled --ngrok-enabled
```

**Using Environment Variable:**

Alternatively, set the `WEBHOOK_ENABLED=true` environment variable. This is often convenient when configuring via MCP client settings (see 'Webhook Configuration in Claude Desktop' below) or in `.env` files.

```bash
# Example for your shell
export WEBHOOK_ENABLED=true
export NGROK_AUTHTOKEN=your_ngrok_token # Also needed for ngrok
telnyx-mcp-server
```

### Ngrok Integration

To enable ngrok tunneling:

1. Get an ngrok authentication token from [ngrok.com](https://ngrok.com/)
2. Set the `NGROK_AUTHTOKEN` environment variable or use the `--ngrok-authtoken` flag:

```bash
# Using NGROK_AUTHTOKEN environment variable (recommended)
export NGROK_AUTHTOKEN=your_ngrok_token
telnyx-mcp-server --webhook-enabled # Or use WEBHOOK_ENABLED=true env var

# Or using --ngrok-authtoken command line flag
telnyx-mcp-server --webhook-enabled --ngrok-authtoken your_ngrok_token
```
If `NGROK_AUTHTOKEN` is set, the `--ngrok-enabled` flag is generally not required when webhooks are active.

When ngrok is enabled, the server will print the public URL that can be used to configure webhooks in the Telnyx Portal.

**Important:** If ngrok fails to initialize (e.g., due to an invalid authtoken, network issues, or conflicts with another ngrok process), the MCP server will exit on startup. Check the server logs for details (see Troubleshooting section).

### Parent Process Monitoring

The MCP server monitors the parent process (Claude Desktop) and automatically exits when the parent process is gone. This ensures proper cleanup of resources even if Claude Desktop closes unexpectedly.


### Webhook Monitoring and Runtime Control

- You can inspect the current webhook and ngrok status by querying the `resource://webhook/info` resource.
- To retrieve a history of received webhook events, use the `get_webhook_events` tool.

### Webhook Configuration in Claude Desktop

To enable webhooks in Claude Desktop, update your configuration:

```json
{
  "mcpServers": {
    "Telnyx": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/team-telnyx/telnyx-mcp-server.git", "telnyx-mcp-server"],
      "env": {
        "TELNYX_API_KEY": "<insert-your-api-key-here>",
        "NGROK_AUTHTOKEN": "<insert-your-ngrok-token-here>",
        "WEBHOOK_ENABLED": "true", // Enables webhooks via environment variable
        // Alternatively, you can use command-line flags in "args" instead of WEBHOOK_ENABLED in env:
        // e.g., "args": ["--from", "git+https://github.com/team-telnyx/telnyx-mcp-server.git", "telnyx-mcp-server", "--webhook-enabled"],
      }
    }
  }
}
```

### Webhook Example

﻿﻿﻿﻿<img width="704" alt="Screenshot Webhook" src="https://github.com/user-attachments/assets/2e1f4a47-df24-4e35-acdf-765ef4a71578" />

## Remote MCP Now Available

Telnyx now offers a remote MCP implementation based on the latest MCP specification. This allows you to access Telnyx's powerful communications APIs through a remotely hosted MCP server. No need to run the server locally. Learn more in the [official documentation](https://developers.telnyx.com/docs/mcp/remote-mcp).

## Contributing

If you want to contribute or run from source:

1. Clone the repository:
```bash
git clone https://github.com/team-telnyx/telnyx-mcp-server.git
cd telnyx-mcp-server
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"  # Includes development dependencies like ruff
```

3. Create a `.env` file and add your Telnyx API key:
```bash
echo "TELNYX_API_KEY=YOUR_API_KEY" > .env
```

4. Run the tests to make sure everything is working:
```bash
pytest
```

5. Install the server in Claude Desktop: `mcp install src/telnyx_mcp_server/server.py`
6. Debug and test locally with MCP Inspector: `mcp dev src/telnyx_mcp_server/server.py`

## Code Quality with Ruff

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting Python code. Ruff is a fast Python linter and formatter written in Rust, designed to replace multiple Python code quality tools with a single, unified tool.

### Installing Ruff

Ruff is included in the development dependencies. Install it with:

```bash
uv pip install -e ".[dev]"
```

### Using Ruff

#### Linting

To check your code for issues:

```bash
ruff check .
```

To automatically fix issues where possible:

```bash
ruff check --fix .
```

#### Formatting

To format your code:

```bash
ruff format .
```

### Pre-commit Workflow

For the best development experience, run these commands before committing changes:

```bash
# Format code
ruff format .

# Fix linting issues
ruff check --fix .

# Run tests
pytest
```

### Configuration

Ruff is configured in the `pyproject.toml` file. The configuration includes:

- Code style rules based on PEP 8
- Import sorting
- Docstring style checking (Google style)
- Code complexity checks
- And more

See the `[tool.ruff]` section in `pyproject.toml` for the complete configuration.

## Troubleshooting

Logs when running with Claude Desktop can be found at:

* **Windows**: `%APPDATA%\Claude\logs\mcp-server-telnyx.log`
* **macOS**: `~/Library/Logs/Claude/mcp-server-telnyx.log`

### MCP Telnyx: spawn uvx ENOENT

If you encounter the error "MCP Telnyx: spawn uvx ENOENT", confirm its absolute path by running this command in your terminal:

```bash
which uvx
```

Once you obtain the absolute path (e.g., `/usr/local/bin/uvx`), update your configuration to use that path (e.g., `"command": "/usr/local/bin/uvx"`). This ensures that the correct executable is referenced.


### Server Fails to Start (Especially with Webhooks/Ngrok)

If the MCP server fails to start, particularly if you have webhooks enabled, it might be due to an issue with ngrok initialization.
One common cause is an existing ngrok process running in the background, potentially from a previous server instance that didn't shut down cleanly.

*   **Check for running processes:** Use commands like `ps aux | grep telnyx-mcp-server` (Linux/macOS) or check Task Manager (Windows) for any lingering `telnyx-mcp-server` processes. Since ngrok is managed internally by the server, you typically won't see a separate 'ngrok' process.
*   **Kill old processes:** If found, terminate these old processes.
*   **Check logs:** Review the server logs (locations mentioned above) for specific error messages related to ngrok or server startup.
