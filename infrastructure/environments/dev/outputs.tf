output "resource_group_name" {
  description = "Main resource group name"
  value       = azurerm_resource_group.main.name
}

output "api_url" {
  description = "Backend API URL"
  value       = module.backend.api_url
}

output "frontend_url" {
  description = "Frontend URL"
  value       = module.frontend.default_url
}

output "database_fqdn" {
  description = "PostgreSQL Server FQDN"
  value       = module.database.server_fqdn
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = module.cache.redis_hostname
}

output "storage_account_name" {
  description = "Storage account name"
  value       = module.storage.storage_account_name
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.keyvault.key_vault_name
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = module.monitoring.application_insights_instrumentation_key
  sensitive   = true
}

output "static_web_app_deployment_token" {
  description = "Static Web App deployment token for GitHub Actions"
  value       = module.frontend.api_key
  sensitive   = true
}
