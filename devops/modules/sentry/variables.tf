# ============================================================================
# Sentry Module Variables
# ============================================================================

# ============================================================================
# Sentry Instance Configuration
# ============================================================================

variable "sentry_url" {
  description = "Sentry instance URL (use http://localhost:9000 for self-hosted, https://sentry.io for SaaS)"
  type        = string
  default     = "http://localhost:9000"
}

variable "sentry_base_url" {
  description = "Sentry backend base URL for provider (must match sentry_url, used for backend requests)"
  type        = string
  default     = "http://localhost:9000"
}

variable "sentry_auth_token" {
  description = <<-EOT
    Sentry authentication token

    Self-hosted: Get from http://localhost:9000/settings/account/security/
                 or via CLI: docker exec -it sentry sentry createtoken

    SaaS: Get from https://sentry.io/settings/account/backend/auth-tokens/

    Required scopes: project:read, project:write, project:admin, org:read
  EOT
  type        = string
  sensitive   = true
}

# Organization Configuration
# ============================================================================

variable "sentry_organization" {
  description = "Sentry organization slug"
  type        = string
  default     = "amazcope"
}

variable "sentry_team" {
  description = "Sentry team slug"
  type        = string
  default     = "engineering"
}

# Project Configuration
# ============================================================================

variable "enable_backend_project" {
  description = "Enable backend (Fastbackend) project"
  type        = bool
  default     = true
}

variable "backend_project_name" {
  description = "Backend project name"
  type        = string
  default     = "Amazcope  Backend"
}

variable "backend_project_slug" {
  description = "Backend project slug"
  type        = string
  default     = "amazcope-backend"
}

variable "enable_frontend_project" {
  description = "Enable frontend (Next.js) project"
  type        = bool
  default     = true
}

variable "frontend_project_name" {
  description = "Frontend project name"
  type        = string
  default     = "Amazcope  Frontend"
}

variable "frontend_project_slug" {
  description = "Frontend project slug"
  type        = string
  default     = "amazcope-frontend"
}

# Alert Configuration
# ============================================================================

variable "enable_alert_rules" {
  description = "Enable alert rules for error spikes"
  type        = bool
  default     = true
}

variable "auto_resolve_age" {
  description = "Auto-resolve issues after N hours of inactivity (0 = disabled)"
  type        = number
  default     = 0
}

# Rate Limiting (Optional)
# ============================================================================

variable "rate_limit_backend" {
  description = "Rate limit for backend project (events per minute, 0 = unlimited)"
  type        = number
  default     = 0
}

variable "rate_limit_frontend" {
  description = "Rate limit for frontend project (events per minute, 0 = unlimited)"
  type        = number
  default     = 0
}
