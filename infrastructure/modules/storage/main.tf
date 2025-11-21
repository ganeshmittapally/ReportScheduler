resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}"
  location                 = var.location
  resource_group_name      = var.resource_group_name
  account_tier             = var.account_tier
  account_replication_type = var.account_replication_type
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false
  
  blob_properties {
    versioning_enabled = var.environment == "prod"
    
    delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }
    
    container_delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }
  }

  tags = var.tags
}

resource "azurerm_storage_container" "reports" {
  name                  = var.container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle management to auto-delete old reports
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "delete-old-reports"
    enabled = true
    
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["${var.container_name}/"]
    }
    
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.lifecycle_delete_after_days
      }
    }
  }
}
