param name string
param location string = resourceGroup().location
param tags object = {}

// Reference to Application Insights
param applicationInsightsName string

// App Service Plan ID
param appServicePlanId string

// OAuth Configuration
@secure()
param azureClientId string

@secure()
param azureClientSecret string

@secure()
param azureTenantId string

@secure()
param jwtSecretKey string

// Telnyx Configuration
@secure()
param telnyxApiKey string

// Environment
param environment string = 'production'

// Reference Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

// Web App
resource web 'Microsoft.Web/sites@2022-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      healthCheckPath: '/health'
      appCommandLine: 'gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 600 --chdir src --access-logfile - --error-logfile - --log-level debug telnyx_mcp_server.remote.server:app'
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
        {
          name: 'XDT_MicrosoftApplicationInsights_Mode'
          value: 'recommended'
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: azureClientId
        }
        {
          name: 'AZURE_CLIENT_SECRET'
          value: azureClientSecret
        }
        {
          name: 'AZURE_TENANT_ID'
          value: azureTenantId
        }
        {
          name: 'AZURE_REDIRECT_URI'
          value: 'https://${name}.azurewebsites.net/auth/callback'
        }
        {
          name: 'JWT_SECRET_KEY'
          value: jwtSecretKey
        }
        {
          name: 'JWT_ALGORITHM'
          value: 'HS256'
        }
        {
          name: 'JWT_EXPIRATION_HOURS'
          value: '24'
        }
        {
          name: 'TELNYX_API_KEY'
          value: telnyxApiKey
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'PYTHON_ENABLE_GUNICORN_MULTIWORKERS'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '0'
        }
      ]
    }
  }
}

// Enable logging
resource webLogs 'Microsoft.Web/sites/config@2022-03-01' = {
  parent: web
  name: 'logs'
  properties: {
    applicationLogs: {
      fileSystem: {
        level: 'Information'
      }
    }
    detailedErrorMessages: {
      enabled: true
    }
    failedRequestsTracing: {
      enabled: true
    }
    httpLogs: {
      fileSystem: {
        enabled: true
        retentionInDays: 1
        retentionInMb: 35
      }
    }
  }
}

output uri string = 'https://${web.properties.defaultHostName}'
output name string = web.name
output principalId string = web.identity.principalId