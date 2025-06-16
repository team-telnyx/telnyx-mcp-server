@description('The location to deploy the resources.')
param location string = resourceGroup().location

@description('The name of the environment (e.g., dev, test, prod). Used for resource naming.')
param environmentName string

@description('The principal ID of the user or service principal deploying the resources. Used to grant Key Vault access for deployment.')
param principalId string = '' // azd automatically populates this

@description('The Telnyx API Key. This will be stored as a secret in Key Vault.')
@secure()
param telnyxApiKey string

// Standard resource naming convention
var appServicePlanName = 'plan-${environmentName}-${uniqueString(resourceGroup().id)}'
var appServiceName = 'app-${environmentName}-${uniqueString(resourceGroup().id)}'
var keyVaultName = 'kv-${environmentName}-${uniqueString(resourceGroup().id)}'
var logAnalyticsWorkspaceName = 'log-${environmentName}-${uniqueString(resourceGroup().id)}'
var keyVaultTelnyxApiSecretName = 'TelnyxApiKey' // Standardized secret name in Key Vault

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux' // Linux App Service Plan
  sku: {
    name: 'B1' // Basic tier for MVP
    tier: 'Basic'
  }
  properties: {
    reserved: true // Required for Linux
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true // Recommended: Use RBAC for data plane access
    // accessPolicies: [] // Clear old access policies if any; RBAC is preferred
  }
}

// Grant the deploying principal (current user/SP) permissions to set secrets during provisioning
resource keyVaultDeploymentPrincipalAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (principalId != '') {
  name: guid(keyVault.id, principalId, 'KeyVaultSecretsOfficer')
  scope: keyVault
  properties: {
    principalId: principalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c1759a0') // Key Vault Secrets Officer
    principalType: 'User' // Or 'ServicePrincipal' if deploying via SP
  }
}


resource telnyxApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: keyVaultTelnyxApiSecretName
  properties: {
    value: telnyxApiKey // The API key passed as a parameter
  }
  dependsOn: [
    keyVaultDeploymentPrincipalAccess // Ensure permissions are set before trying to write secret
  ]
}

resource appService 'Microsoft.Web/sites@2022-09-01' = {
  name: appServiceName
  location: location
  kind: 'app,linux' // Web app on Linux
  identity: {
    type: 'SystemAssigned' // Enable System Assigned Managed Identity for Key Vault access
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true // Enforce HTTPS
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11' // Specify Python 3.11
      pythonVersion: '3.11'
      alwaysOn: true // Keep the app alive for B1 SKU and above
      ftpsState: 'FtpsOnly'
      appSettings: [
        {
          name: 'TELNYX_API_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${telnyxApiKeySecret.properties.secretUriWithVersion})'
        }
        {
          name: 'WEBHOOK_ENABLED'
          value: 'true'
        }
        {
          name: 'TELNYX_MCP_SERVER_BASE_URL'
          value: 'https://${appServiceName}.azurewebsites.net'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT' // azd handles build, Oryx will run on App Service
          value: 'true' // Let Oryx build the application on deploy
        }
        {
          name: 'WEBSITES_PORT' // Port your application listens on
          value: '8000' // Default for many Python web frameworks; FastAPI uses this
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING' // For App Insights integration via Log Analytics
          value: reference(logAnalyticsWorkspace.id, '2022-10-01').instrumentationKey // This might need to be the full connection string
        }
        // Add other necessary environment variables here
      ]
      startupCommand: 'python -m telnyx_mcp_server.server --host 0.0.0.0 --port ${PORT:-8000}' // Startup command for Telnyx MCP Server
      // Assumes Telnyx MCP Server uses Poetry and pyproject.toml, which Oryx can build.
      // If `uv` is strictly needed for runtime and not just dev/build, a Dockerfile might be better.
    }
  }
}

// Grant App Service's Managed Identity access to Key Vault secrets
resource keyVaultAppServiceAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appService.id, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    principalId: appService.identity.principalId
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_APP_SERVICE_ENDPOINT string = 'https://${appService.properties.defaultHostName}'
output AZURE_KEY_VAULT_NAME string = keyVault.name
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.properties.vaultUri
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appService.properties.siteConfig.appSettings[?name == 'APPLICATIONINSIGHTS_CONNECTION_STRING'].value