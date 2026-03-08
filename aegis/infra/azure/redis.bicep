// ──────────────────────────────────────────────
// AEGIS — Azure Cache for Redis (Bicep)
// ──────────────────────────────────────────────

@description('Redis cache name')
param redisCacheName string = 'aegis-redis'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Redis SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param skuName string = 'Standard'

resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: redisCacheName
  location: location
  properties: {
    sku: {
      name: skuName
      family: skuName == 'Premium' ? 'P' : 'C'
      capacity: skuName == 'Basic' ? 0 : 1
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

output redisHostName string = redisCache.properties.hostName
output redisSslPort int = redisCache.properties.sslPort
output redisConnectionString string = '${redisCache.properties.hostName}:${redisCache.properties.sslPort},password=${redisCache.listKeys().primaryKey},ssl=True,abortConnect=False'
