output "resource_group_name" {
  description = "Network resource group name"
  value       = azurerm_resource_group.network.name
}

output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Virtual Network name"
  value       = azurerm_virtual_network.main.name
}

output "subnet_app_id" {
  description = "App subnet ID"
  value       = azurerm_subnet.app.id
}

output "subnet_data_id" {
  description = "Data subnet ID"
  value       = azurerm_subnet.data.id
}

output "subnet_private_endpoints_id" {
  description = "Private endpoints subnet ID"
  value       = azurerm_subnet.private_endpoints.id
}
