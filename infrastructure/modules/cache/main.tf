resource "azurerm_redis_cache" "main" {
  name                = "redis-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  capacity            = var.capacity
  family              = var.family
  sku_name            = var.sku_name
  enable_non_ssl_port = var.enable_non_ssl_port
  minimum_tls_version = "1.2"
  
  redis_configuration {
    maxmemory_reserved = var.sku_name == "Premium" ? 50 : 10
    maxmemory_delta    = var.sku_name == "Premium" ? 50 : 10
    maxmemory_policy   = "allkeys-lru"
  }

  tags = var.tags
}
