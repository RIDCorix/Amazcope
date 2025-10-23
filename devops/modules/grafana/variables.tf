# ============================================================================
# Grafana Module Variables
# ============================================================================

# Grafana Connection
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

# Optional: Import official dashboards from grafana.com
# Requires downloading JSON files to dashboards/ directory
variable "import_k6_official_dashboard" {
  description = "Import official k6 dashboard from grafana.com (ID: 2587)"
  type        = bool
  default     = false
}

variable "import_node_exporter_official_dashboard" {
  description = "Import official Node Exporter dashboard from grafana.com (ID: 1860)"
  type        = bool
  default     = false
}

# ============================================================================
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
