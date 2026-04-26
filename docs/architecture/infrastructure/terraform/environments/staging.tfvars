environment = "staging"
location    = "centralus"

common_tags = {
  Project     = "NoteKeeper"
  ManagedBy   = "Terraform"
  Environment = "staging"
}

# PostgreSQL Staging Configuration
postgres_sku_name   = "B_Standard_B2s"
postgres_storage_mb = 32768

# Redis Staging Configuration
redis_capacity = 1
redis_family   = "C"
redis_sku      = "Standard"

# App Service Staging Configuration
appservice_sku_name = "B2"

cors_allowed_origins = [
  "https://staging.notekeeper.bhogarai.com",
  "http://localhost:3000",
  "http://localhost:5173"
]

log_level = "DEBUG"
