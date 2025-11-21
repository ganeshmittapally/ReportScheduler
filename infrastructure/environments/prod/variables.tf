variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
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
}

variable "worker_image" {
  description = "Backend worker container image"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    environment = "prod"
    project     = "reportscheduler"
    owner       = "platform-team"
    terraform   = "true"
    cost_center = "engineering"
  }
}
