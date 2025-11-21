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

variable "subnet_id" {
  description = "Subnet ID for Container App Environment"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  type        = string
}

variable "application_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

variable "container_registry_server" {
  description = "Container registry server URL"
  type        = string
  default     = ""
}

variable "api_image" {
  description = "Backend API container image"
  type        = string
}

variable "worker_image" {
  description = "Backend worker container image"
  type        = string
}

variable "api_cpu" {
  description = "API CPU allocation"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "API memory allocation"
  type        = string
  default     = "1Gi"
}

variable "worker_cpu" {
  description = "Worker CPU allocation"
  type        = number
  default     = 1.0
}

variable "worker_memory" {
  description = "Worker memory allocation"
  type        = string
  default     = "2Gi"
}

variable "api_min_replicas" {
  description = "Minimum API replicas"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum API replicas"
  type        = number
  default     = 10
}

variable "worker_min_replicas" {
  description = "Minimum worker replicas"
  type        = number
  default     = 1
}

variable "worker_max_replicas" {
  description = "Maximum worker replicas"
  type        = number
  default     = 30
}

variable "environment_variables" {
  description = "Environment variables for containers"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secret environment variables"
  type = map(object({
    name  = string
    value = string
  }))
  default   = {}
  sensitive = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
