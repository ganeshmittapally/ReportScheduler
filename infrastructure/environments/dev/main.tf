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
  vnet_address_space  = ["10.0.0.0/16"]
  
  subnet_app = {
    name             = "snet-app"
    address_prefixes = ["10.0.1.0/24"]
  }
  
  subnet_data = {
    name             = "snet-data"
    address_prefixes = ["10.0.2.0/24"]
  }
  
  subnet_private_endpoints = {
    name             = "snet-pe"
    address_prefixes = ["10.0.3.0/24"]
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
  log_retention_days   = 30
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
  sku_name                      = "B_Standard_B1ms"
  storage_mb                    = 32768
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  tags                          = var.tags
}

# Cache Module (Redis)
module "cache" {
  source = "../../modules/cache"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  sku_name             = "Basic"
  family               = "C"
  capacity             = 0
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
  account_replication_type     = "LRS"
  container_name               = "reports"
  lifecycle_delete_after_days  = 30
  tags                         = var.tags
}

# Messaging Module (Service Bus)
module "messaging" {
  source = "../../modules/messaging"

  environment          = var.environment
  location             = var.location
  project_name         = var.project_name
  resource_group_name  = azurerm_resource_group.main.name
  sku                  = "Standard"
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
  
  api_cpu             = 0.5
  api_memory          = "1Gi"
  api_min_replicas    = 1
  api_max_replicas    = 3
  
  worker_cpu          = 1.0
  worker_memory       = "2Gi"
  worker_min_replicas = 1
  worker_max_replicas = 10

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
  sku_tier             = "Free"
  sku_size             = "Free"
  api_url              = module.backend.api_url
  tags                 = var.tags
}
