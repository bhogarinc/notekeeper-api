variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "centralus"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "NoteKeeper"
    ManagedBy   = "Terraform"
    Environment = ""
  }
}

# PostgreSQL Variables
variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  sensitive   = true
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "postgres_sku_name" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768
}

# Redis Variables
variable "redis_capacity" {
  description = "Redis capacity"
  type        = number
  default     = 1
}

variable "redis_family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "redis_sku" {
  description = "Redis SKU"
  type        = string
  default     = "Basic"
}

# App Service Variables
variable "appservice_sku_name" {
  description = "App Service Plan SKU"
  type        = string
  default     = "B1"
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "cors_allowed_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}

# Application Variables
variable "app_secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "azure_storage_connection_string" {
  description = "Azure Storage connection string"
  type        = string
  sensitive   = true
  default     = ""
}

# Monitoring Variables
variable "alert_email_addresses" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}
