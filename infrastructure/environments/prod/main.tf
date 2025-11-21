data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
  tags     = var.tags
}

# Network Module
module "network" {
  source = "../../modules/network"

  environment         = var.environment
  location            = var.location
  project_name        = var.project_name
  vnet_address_space  = ["10.1.0.0/16"]
  
  subnet_app = {
    name             = "snet-app"
    address_prefixes = ["10.1.1.0/24"]
  }
  
  subnet_data = {
    name             = "snet-data"
    address_prefixes = ["10.1.2.0/24"]
  }
  
  subnet_private_endpoints = {
    name             = "snet-pe"
    address_prefixes = ["10.1.3.0/24"]
  }
  
  tags = var.tags
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  log_retention_days   = 90
  tags                 = var.tags
}

# Key Vault Module
module "keyvault" {
  source = "../../modules/keyvault"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  tenant_id            = var.tenant_id
  subnet_id            = module.network.subnet_private_endpoints_id
  tags                 = var.tags
}

# Database Module (PostgreSQL)
module "database" {
  source = "../../modules/database"

  environment                   = var.environment
  location                      = var.location
  project_name                  = var.project_name
  resource_group_name           = azurerm_resource_group.main.name
  subnet_id                     = module.network.subnet_data_id
  sku_name                      = "GP_Standard_D4s_v3"
  storage_mb                    = 131072  # 128 GB
  backup_retention_days         = 35
  geo_redundant_backup_enabled  = true
  tags                          = var.tags
}

# Cache Module (Redis)
module "cache" {
  source = "../../modules/cache"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  sku_name             = "Premium"
  family               = "P"
  capacity             = 1
  tags                 = var.tags
}

# Storage Module (Blob Storage)
module "storage" {
  source = "../../modules/storage"

  environment                  = var.environment
  location                     = var.location
  project_name                 = var.project_name
  resource_group_name          = azurerm_resource_group.main.name
  account_tier                 = "Standard"
  account_replication_type     = "GRS"  # Geo-redundant
  container_name               = "reports"
  lifecycle_delete_after_days  = 90
  tags                         = var.tags
}

# Messaging Module (Service Bus)
module "messaging" {
  source = "../../modules/messaging"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  sku                  = "Premium"
  tags                 = var.tags
}

# Backend Compute Module (Container Apps)
module "backend" {
  source = "../../modules/compute/backend"

  environment                            = var.environment
  location                               = var.location
  project_name                           = var.project_name
  resource_group_name                    = azurerm_resource_group.main.name
  subnet_id                              = module.network.subnet_app_id
  log_analytics_workspace_id             = module.monitoring.log_analytics_workspace_id
  application_insights_connection_string = module.monitoring.application_insights_connection_string
  
  api_image    = var.api_image
  worker_image = var.worker_image
  
  api_cpu             = 1.0
  api_memory          = "2Gi"
  api_min_replicas    = 3
  api_max_replicas    = 20
  
  worker_cpu          = 2.0
  worker_memory       = "4Gi"
  worker_min_replicas = 5
  worker_max_replicas = 50

  environment_variables = {
    ENVIRONMENT = var.environment
  }

  secrets = {
    database-url = {
      name  = "DATABASE_URL"
      value = module.database.connection_string
    }
    redis-url = {
      name  = "REDIS_URL"
      value = module.cache.redis_connection_string
    }
    storage-connection = {
      name  = "AZURE_STORAGE_CONNECTION_STRING"
      value = module.storage.primary_connection_string
    }
    servicebus-connection = {
      name  = "SERVICEBUS_CONNECTION_STRING"
      value = module.messaging.primary_connection_string
    }
  }

  tags = var.tags
}

# Frontend Module (Static Web App)
module "frontend" {
  source = "../../modules/compute/frontend"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  sku_tier             = "Standard"
  sku_size             = "Standard"
  api_url              = module.backend.api_url
  tags                 = var.tags
}
