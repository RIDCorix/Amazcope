# ============================================================================
# DevOps Infrastructure Variables
# ============================================================================

# Grafana Authentication
# ============================================================================

variable "grafana_url" {
  description = "The URL of the Grafana instance"
  type        = string
  default     = "http://localhost:3000"
}

variable "grafana_auth" {
  description = "Basic authentication for Grafana (format: username:password)"
  type        = string
  default     = "admin:admin"
  sensitive   = true
}

variable "grafana_backend_key" {
  description = "Grafana backend key (alternative to basic auth, recommended for production)"
  type        = string
  default     = ""
  sensitive   = true
}

# InfluxDB Configuration
# ============================================================================

variable "influxdb_url" {
  description = "The URL of the InfluxDB instance"
  type        = string
  default     = "http://influxdb:8086"
}

variable "influxdb_database" {
  description = "The name of the InfluxDB database for k6 metrics"
  type        = string
  default     = "k6"
}

variable "influxdb_username" {
  description = "InfluxDB username (optional, leave empty if no auth)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "influxdb_password" {
  description = "InfluxDB password (optional, leave empty if no auth)"
  type        = string
  default     = ""
  sensitive   = true
}

# Prometheus Configuration
# ============================================================================

variable "prometheus_url" {
  description = "The URL of the Prometheus instance"
  type        = string
  default     = "http://prometheus:9090"
}

variable "prometheus_basic_auth_user" {
  description = "Prometheus basic auth username (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "prometheus_basic_auth_password" {
  description = "Prometheus basic auth password (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

# Feature Flags
# ============================================================================

variable "enable_influxdb" {
  description = "Enable InfluxDB datasource creation"
  type        = bool
  default     = true
}

variable "enable_prometheus" {
  description = "Enable Prometheus datasource creation"
  type        = bool
  default     = true
}

variable "influxdb_is_default" {
  description = "Set InfluxDB as the default datasource"
  type        = bool
  default     = true
}

variable "prometheus_is_default" {
  description = "Set Prometheus as the default datasource"
  type        = bool
  default     = false
}

# Dashboard Configuration
# ============================================================================

variable "enable_k6_dashboard" {
  description = "Enable k6 load testing dashboard"
  type        = bool
  default     = true
}

variable "enable_node_exporter_dashboard" {
  description = "Enable Node Exporter system metrics dashboard"
  type        = bool
  default     = true
}

variable "enable_cadvisor_dashboard" {
  description = "Enable cAdvisor container metrics dashboard"
  type        = bool
  default     = true
}

variable "import_k6_official_dashboard" {
  description = "Import official k6 dashboard from grafana.com (ID: 2587)"
  type        = bool
  default     = false
}

# Alerting Configuration
# ============================================================================

variable "enable_alerting" {
  description = "Enable Grafana alerting (unified alerting)"
  type        = bool
  default     = true
}

variable "alert_email_addresses" {
  description = "List of email addresses to receive alert notifications"
  type        = list(string)
  default     = ["admin@example.com"]
}

variable "alert_slack_webhook_url" {
  description = "Slack webhook URL for alert notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alert_webhook_url" {
  description = "Custom webhook URL for alert notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "import_node_exporter_official_dashboard" {
  description = "Import official Node Exporter dashboard from grafana.com (ID: 1860)"
  type        = bool
  default     = false
}

# ============================================================================
# Sentry Configuration
# ============================================================================

# Sentry Instance Configuration
# ----------------------------------------------------------------------------

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
  description = "Sentry authentication token (self-hosted: http://localhost:9000/settings/account/security/, SaaS: https://sentry.io/settings/account/backend/auth-tokens/)"
  type        = string
  default     = ""
  sensitive   = true
}

# Organization and Team
# ----------------------------------------------------------------------------

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

# Backend Project Configuration
# ----------------------------------------------------------------------------

variable "enable_backend_sentry" {
  description = "Enable backend (Fastbackend) Sentry project"
  type        = bool
  default     = true
}

variable "sentry_backend_project_name" {
  description = "Backend Sentry project name"
  type        = string
  default     = "Amazcope  Backend"
}

variable "sentry_backend_project_slug" {
  description = "Backend Sentry project slug"
  type        = string
  default     = "amazcope-backend"
}

# Frontend Project Configuration
# ----------------------------------------------------------------------------

variable "enable_frontend_sentry" {
  description = "Enable frontend (Next.js) Sentry project"
  type        = bool
  default     = true
}

variable "sentry_frontend_project_name" {
  description = "Frontend Sentry project name"
  type        = string
  default     = "Amazcope  Frontend"
}

variable "sentry_frontend_project_slug" {
  description = "Frontend Sentry project slug"
  type        = string
  default     = "amazcope-frontend"
}

# Alert Configuration
# ----------------------------------------------------------------------------

variable "enable_sentry_alerts" {
  description = "Enable Sentry alert rules for error spikes"
  type        = bool
  default     = true
}

variable "sentry_auto_resolve_age" {
  description = "Auto-resolve issues after N hours of inactivity (0 = disabled)"
  type        = number
  default     = 0
}

# ============================================================================
# Future Module Variables (Uncomment when needed)
# ============================================================================

# variable "datadog_backend_key" {
#   description = "Datadog backend key"
#   type        = string
#   default     = ""
#   sensitive   = true
# }

# variable "datadog_app_key" {
#   description = "Datadog application key"
#   type        = string
#   default     = ""
#   sensitive   = true
# }

# variable "pagerduty_token" {
#   description = "PagerDuty backend token"
#   type        = string
#   default     = ""
#   sensitive   = true
# }
