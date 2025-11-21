output "container_app_environment_id" {
  description = "Container App Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "api_fqdn" {
  description = "API FQDN"
  value       = azurerm_container_app.api.ingress[0].fqdn
}

output "api_url" {
  description = "API URL"
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "api_container_app_id" {
  description = "API Container App ID"
  value       = azurerm_container_app.api.id
}

output "worker_container_app_id" {
  description = "Worker Container App ID"
  value       = azurerm_container_app.worker.id
}
