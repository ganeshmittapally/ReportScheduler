output "static_web_app_id" {
  description = "Static Web App ID"
  value       = azurerm_static_web_app.main.id
}

output "default_host_name" {
  description = "Default hostname"
  value       = azurerm_static_web_app.main.default_host_name
}

output "default_url" {
  description = "Default URL"
  value       = "https://${azurerm_static_web_app.main.default_host_name}"
}

output "api_key" {
  description = "Static Web App deployment token"
  value       = azurerm_static_web_app.main.api_key
  sensitive   = true
}
