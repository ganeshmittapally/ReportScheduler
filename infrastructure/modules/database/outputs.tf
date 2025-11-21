output "server_id" {
  description = "PostgreSQL Server ID"
  value       = azurerm_postgresql_flexible_server.main.id
}

output "server_name" {
  description = "PostgreSQL Server name"
  value       = azurerm_postgresql_flexible_server.main.name
}

output "server_fqdn" {
  description = "PostgreSQL Server FQDN"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "database_name" {
  description = "Database name"
  value       = azurerm_postgresql_flexible_server_database.reportscheduler.name
}

output "administrator_login" {
  description = "Admin username"
  value       = azurerm_postgresql_flexible_server.main.administrator_login
}

output "administrator_password" {
  description = "Admin password"
  value       = random_password.postgres.result
  sensitive   = true
}

output "connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.reportscheduler.name}?sslmode=require"
  sensitive   = true
}
