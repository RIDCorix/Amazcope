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

# ============================================================================
# Dashboard Configuration
# ============================================================================

variable "enable_k6_dashboard" {
  description = "Enable k6 load testing dashboard"
  type        = bool
  default     = true
}

variable "enable_cadvisor_dashboard" {
  description = "Enable cAdvisor container metrics dashboard"
  type        = bool
  default     = true
}

# Optional: Import official dashboards from grafana.com
# Requires downloading JSON files to dashboards/ directory
variable "import_k6_official_dashboard" {
  description = "Import official k6 dashboard from grafana.com (ID: 2587)"
  type        = bool
  default     = false
}

# ============================================================================
# Sentry Configuration
# ============================================================================

variable "enable_sentry" {
  description = "Enable Sentry datasource creation"
  type        = bool
  default     = false
}

variable "sentry_url" {
  description = "The URL of the Sentry instance"
  type        = string
  default     = "https://sentry.io"
}

variable "sentry_org_slug" {
  description = "Sentry organization slug"
  type        = string
  default     = ""
}

variable "sentry_auth_token" {
  description = "Sentry authentication token (required if enable_sentry = true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_sentry_dashboard" {
  description = "Enable Sentry error tracking dashboard"
  type        = bool
  default     = true
}
