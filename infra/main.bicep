targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string

// OAuth and application configuration parameters
@description('Azure OAuth Client ID')
param azureClientId string = ''

@secure()
@description('Azure OAuth Client Secret')
param azureClientSecret string = ''

@description('Azure Tenant ID')
param azureTenantId string = ''

@secure()
@description('JWT Secret Key for token signing')
param jwtSecretKey string = ''

@secure()
@description('Telnyx API Key')
param telnyxApiKey string = ''

@description('Application Environment')
param environment string = 'production'

// Optional parameters to override the default azd resource naming conventions
param resourceGroupName string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// The application frontend
module web './app/web.bicep' = {
  name: 'web'
  scope: rg
  params: {
    name: '${abbrs.webSitesAppService}web-${resourceToken}'
    location: location
    tags: tags
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    appServicePlanId: appServicePlan.outputs.id
    // OAuth parameters
    azureClientId: azureClientId
    azureClientSecret: azureClientSecret
    azureTenantId: azureTenantId
    jwtSecretKey: jwtSecretKey
    // Telnyx parameters
    telnyxApiKey: telnyxApiKey
    environment: environment
  }
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan './core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'  // Basic tier for MVP
      capacity: 1
    }
    kind: 'linux'
    reserved: true
  }
}

// Monitor application with Azure Monitor
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

// App outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output WEB_URI string = web.outputs.uri
output RESOURCE_GROUP string = rg.name