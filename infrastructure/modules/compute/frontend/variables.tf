variable "environment" {
  description = "Environment name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "sku_tier" {
  description = "Static Web App SKU tier (Free or Standard)"
  type        = string
  default     = "Free"
}

variable "sku_size" {
  description = "Static Web App SKU size (Free or Standard)"
  type        = string
  default     = "Free"
}

variable "api_url" {
  description = "Backend API URL"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
