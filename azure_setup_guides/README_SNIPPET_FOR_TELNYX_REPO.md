---

## Azure Deployment using Azure Developer CLI (`azd`)

This section describes how to deploy the Telnyx MCP Server to Azure App Service using the Azure Developer CLI (`azd`). The `azd` templates for this are included in this repository.

### Prerequisites

1.  [Azure Developer CLI (`azd`)](https://aka.ms/install-azd) installed.
2.  [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) installed and logged in (`az login`).
3.  [Python 3.10+](https://www.python.org/downloads/) (as per `telnyx-mcp-server` requirements).
4.  [Poetry](https://python-poetry.org/docs/#installation) (for local Python dependency management).
5.  A Telnyx API Key.
6.  You must be in the root directory of this `telnyx-mcp-server` repository clone.

### Setup and Deployment to Azure

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/team-telnyx/telnyx-mcp-server.git
    cd telnyx-mcp-server
    ```

2.  **Login to Azure via `azd`:**
    This command will open a browser window for you to authenticate.
    ```bash
    azd auth login
    ```

3.  **Initialize `azd` environment:**
    This command initializes the project for `azd`, creating a new environment (e.g., `my-mcp-dev`). It will prompt you for an environment name, Azure subscription, and Azure region.
    ```bash
    azd init
    ```
    *(If you already have an azd environment from a previous setup in this directory, you can use `azd env select <your-env-name>` or `azd env new <new-env-name>`)*

4.  **Set your Telnyx API Key:**
    This key is essential for the server to function. `azd` will store it securely and make it available to your Azure App Service via Azure Key Vault.
    ```bash
    azd env set TELNYX_API_KEY "YOUR_TELNYX_API_KEY_HERE" --secret
    ```
    You can also set your preferred Azure location if you didn't during `init`:
    ```bash
    # azd env set AZURE_LOCATION "eastus" # Example: set preferred Azure region
    ```

5.  **Provision infrastructure and deploy the application:**
    This single command will:
    *   Package the `telnyx-mcp-server` application.
    *   Provision all necessary Azure resources (App Service, Key Vault, Log Analytics) as defined in the `infra/` folder.
    *   Deploy the packaged application to the newly created App Service.
    *   Configure application settings, including the `TELNYX_API_KEY` from Key Vault.
    ```bash
    azd up
    ```
    This process can take several minutes, especially on the first run. `azd` will stream logs and show progress. Once complete, it will output the URL of your deployed application.

### Local Development (Using Poetry)

To run the Telnyx MCP server locally (as per the main project instructions):

1.  Ensure Poetry is installed and you are in the `telnyx-mcp-server` root directory.
2.  Install dependencies:
    ```bash
    poetry install
    ```
3.  Create a `.env` file in the project root with your `TELNYX_API_KEY` and other settings:
    ```env
    TELNYX_API_KEY="your_telnyx_api_key"
    WEBHOOK_ENABLED="true" # Or false
    TELNYX_MCP_SERVER_BASE_URL="http://localhost:8000" # For local testing
    # Add other env vars as needed by the server (see src/telnyx_mcp_server/config.py)
    ```
4.  Run the server using Poetry:
    ```bash
    poetry run python -m telnyx_mcp_server.server --port 8000
    ```

### Accessing Your Deployed Application

After `azd up` successfully completes, `azd` will print the endpoint URL for your App Service. You can use this URL to interact with your deployed Telnyx MCP Server.

Example (Health Check):
`curl https://<your-app-name>.azurewebsites.net/health`

### Updating the Deployment

If you make changes to the `telnyx-mcp-server` code or the `azd` configuration:
1. Commit your changes to git.
2. Run `azd deploy` to deploy code changes.
3. Run `azd provision` if you've changed infrastructure (Bicep files). Or simply run `azd up` again which handles both.

### Clean Up Azure Resources

To delete all Azure resources created by this `azd` template for a specific environment:
```bash
azd down
```
To also purge resources that support soft-delete (like Key Vault) immediately:
```bash
azd down --purge --force
```
*(Use `--purge` with caution as it permanently deletes resources.)*