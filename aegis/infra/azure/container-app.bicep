// ──────────────────────────────────────────────
// AEGIS — Azure Container Apps (Bicep)
// Infrastructure as Code for Azure deployment
// ──────────────────────────────────────────────

@description('Environment name for resource naming')
param environmentName string = 'aegis-prod'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Container registry login server')
param containerRegistryServer string

@description('Backend container image')
param backendImage string = 'aegis-backend:latest'

@description('Frontend container image')
param frontendImage string = 'aegis-frontend:latest'

@description('Redis connection string')
@secure()
param redisConnectionString string

@description('Azure OpenAI endpoint (optional)')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI API key (optional)')
@secure()
param azureOpenAIApiKey string = ''

// ─── Container Apps Environment ──────────────
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${environmentName}-env'
  location: location
  properties: {
    zoneRedundant: false
  }
}

// ─── Backend Container App ──────────────────
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${environmentName}-backend'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
      }
      secrets: [
        { name: 'redis-url', value: redisConnectionString }
        { name: 'openai-key', value: azureOpenAIApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${containerRegistryServer}/${backendImage}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            { name: 'REDIS_URL', secretRef: 'redis-url' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'openai-key' }
            { name: 'APP_ENV', value: 'production' }
            { name: 'DEBUG', value: 'false' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// ─── Worker Container App ───────────────────
resource workerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${environmentName}-worker'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      secrets: [
        { name: 'redis-url', value: redisConnectionString }
        { name: 'openai-key', value: azureOpenAIApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${containerRegistryServer}/${backendImage}'
          command: ['python', '-m', 'workers.scan_worker']
          resources: {
            cpu: json('2.0')
            memory: '4Gi'
          }
          env: [
            { name: 'REDIS_URL', secretRef: 'redis-url' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'openai-key' }
            { name: 'APP_ENV', value: 'production' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

// ─── Frontend Container App ─────────────────
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${environmentName}-frontend'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: '${containerRegistryServer}/${frontendImage}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'NEXT_PUBLIC_API_URL'
              value: 'https://${backendApp.properties.configuration.ingress.fqdn}/api/v1'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// ─── Outputs ────────────────────────────────
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
