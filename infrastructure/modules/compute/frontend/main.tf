resource "azurerm_static_web_app" "main" {
  name                = "stapp-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = var.sku_tier
  sku_size            = var.sku_size
  tags                = var.tags

  app_settings = {
    VITE_API_BASE_URL = var.api_url
  }
}

# Custom domain (optional, for production)
# Uncomment and configure if you have a custom domain
# resource "azurerm_static_web_app_custom_domain" "main" {
#   count               = var.environment == "prod" ? 1 : 0
#   static_web_app_id   = azurerm_static_web_app.main.id
#   domain_name         = "reports.example.com"
#   validation_type     = "cname-delegation"
# }
