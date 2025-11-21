output "namespace_id" {
  description = "Service Bus Namespace ID"
  value       = azurerm_servicebus_namespace.main.id
}

output "namespace_name" {
  description = "Service Bus Namespace name"
  value       = azurerm_servicebus_namespace.main.name
}

output "primary_connection_string" {
  description = "Primary connection string"
  value       = azurerm_servicebus_namespace.main.default_primary_connection_string
  sensitive   = true
}

output "report_tasks_queue_name" {
  description = "Report tasks queue name"
  value       = azurerm_servicebus_queue.report_tasks.name
}

output "email_tasks_queue_name" {
  description = "Email tasks queue name"
  value       = azurerm_servicebus_queue.email_tasks.name
}
