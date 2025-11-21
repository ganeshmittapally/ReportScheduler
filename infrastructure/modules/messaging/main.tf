resource "azurerm_servicebus_namespace" "main" {
  name                = "sb-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  capacity            = var.sku == "Premium" ? 1 : 0
  tags                = var.tags
}

# Queue for report generation tasks
resource "azurerm_servicebus_queue" "report_tasks" {
  name         = "report-generation-tasks"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_size_in_megabytes                = 1024
  default_message_ttl                  = "P14D"  # 14 days
  lock_duration                        = "PT5M"  # 5 minutes
  max_delivery_count                   = 10
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
}

# Queue for email delivery tasks
resource "azurerm_servicebus_queue" "email_tasks" {
  name         = "email-delivery-tasks"
  namespace_id = azurerm_servicebus_namespace.main.id

  max_size_in_megabytes                = 1024
  default_message_ttl                  = "P7D"  # 7 days
  lock_duration                        = "PT2M"  # 2 minutes
  max_delivery_count                   = 5
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
}
