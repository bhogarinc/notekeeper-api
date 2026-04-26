environment = "production"
location    = "centralus"

common_tags = {
  Project     = "NoteKeeper"
  ManagedBy   = "Terraform"
  Environment = "production"
  CostCenter  = "engineering"
}

# PostgreSQL Production Configuration
postgres_sku_name   = "GP_Standard_D2s_v3"
postgres_storage_mb = 65536

# Redis Production Configuration
redis_capacity = 1
redis_family   = "P"
redis_sku      = "Premium"

# App Service Production Configuration
appservice_sku_name = "P1v3"

cors_allowed_origins = [
  "https://notekeeper.bhogarai.com",
  "https://app.notekeeper.bhogarai.com"
]

log_level = "INFO"
