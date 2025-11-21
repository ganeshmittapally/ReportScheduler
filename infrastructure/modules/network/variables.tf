variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "reportscheduler"
}

variable "vnet_address_space" {
  description = "VNet address space"
  type        = list(string)
}

variable "subnet_app" {
  description = "App subnet configuration"
  type = object({
    name             = string
    address_prefixes = list(string)
  })
}

variable "subnet_data" {
  description = "Data subnet configuration"
  type = object({
    name             = string
    address_prefixes = list(string)
  })
}

variable "subnet_private_endpoints" {
  description = "Private endpoints subnet configuration"
  type = object({
    name             = string
    address_prefixes = list(string)
  })
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
