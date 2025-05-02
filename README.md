# Telnyx Local Model Context Protocol (MCP) Server

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

## Example Usage

Try asking Claude:

* "Create an AI agent that can handle customer service for an e-commerce business"
* "Send a text message to +5555551234 saying 'Your appointment is confirmed for tomorrow at 3pm'"
* "Make a call to my customer at +5555551234 and transfer them to my support team"
* "Find me a phone number in Chicago with area code 312"
* "Create an auto-attendant system using Telnyx AI assistants and voice features"
* "Upload /Volumes/Drive/contract.pdf to the 'legal-docs' bucket in Telnyx Cloud Storage"
* "Embed the knowledge base at https://example.com/docs so the assistant can answer user questions"
* "Create a integration secret named openai-token with my openai key XYZ"

## Coming Soon

Telnyx is working on a remote MCP implementation with OAuth authentication based on the latest MCP specification. This will enable access to Telnyx's powerful communications APIs through a remotely hosted server without having to run the MCP server locally.

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
uv pip install -e .
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