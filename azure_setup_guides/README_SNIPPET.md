## Telnyx MCP Server Azure Deployment (`azd`)

This project includes an Azure Developer CLI (`azd`) template to deploy the Telnyx MCP Server to Azure App Service.

### Prerequisites

1.  [Azure Developer CLI (`azd`)](https://aka.ms/install-azd)
2.  [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) (logged in: `az login`)
3.  [Python 3.10+](https://www.python.org/downloads/)
4.  [Poetry](https://python-poetry.org/docs/#installation) (for local Python dependency management, if you modify the code)
5.  A Telnyx API Key.

### Local Development & Setup (One-time)

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/team-telnyx/telnyx-mcp-server.git
    cd telnyx-mcp-server
    # (Or your fork/project location where these azd files are)
    ```

2.  **Login to Azure via `azd`:**
    ```bash
    azd auth login
    ```

3.  **Initialize `azd` environment (creates `.azure` folder):**
    This step will prompt you for an environment name, subscription, and location.
    ```bash
    azd init
    # Or if you already have the files and want to create a new environment:
    # azd env new my-mcp-app-dev  # (replace with your desired environment name)
    ```

4.  **Set your Telnyx API Key:**
    This key will be stored securely by `azd` and provisioned into Azure Key Vault.
    ```bash
    azd env set TELNYX_API_KEY "YOUR_TELNYX_API_KEY_HERE" --secret
    ```
    You can also set your preferred Azure location if not done during `init`:
    ```bash
    # azd env set AZURE_LOCATION "eastus" # Or your preferred region
    ```

### Deploy to Azure

1.  **Provision infrastructure and deploy the application:**
    This command will package the application, create all necessary Azure resources (App Service, Key Vault, etc.), and deploy the code.
    ```bash
    azd up
    ```
    This process might take several minutes. `azd` will stream logs and show progress.

### Run Locally (Optional, for testing server logic)

To run the Telnyx MCP server locally (independent of `azd` deployment):
1.  Ensure Poetry is installed.
2.  Install dependencies: `poetry install`
3.  Create a `.env` file in the project root with your `TELNYX_API_KEY` and other settings:
    ```env
    TELNYX_API_KEY="your_telnyx_api_key"
    WEBHOOK_ENABLED="true" # Or false
    TELNYX_MCP_SERVER_BASE_URL="http://localhost:8000"
    # Add other env vars as needed by the server
    ```
4.  Run the server using Poetry:
    ```bash
    poetry run python -m telnyx_mcp_server.server --port 8000
    ```

### Clean Up Resources

To delete all Azure resources created by this deployment for a specific environment:
```bash
azd down --purge --force
```
(Be cautious with `--purge` as it permanently deletes Key Vaults without soft-delete)