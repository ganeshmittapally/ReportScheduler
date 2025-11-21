variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "reportscheduler"
}

variable "tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
}

variable "api_image" {
  description = "Backend API container image"
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "worker_image" {
  description = "Backend worker container image"
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    environment = "dev"
    project     = "reportscheduler"
    owner       = "platform-team"
    terraform   = "true"
  }
}
