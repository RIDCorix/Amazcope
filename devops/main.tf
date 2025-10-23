# ============================================================================
# Amazcope DevOps Infrastructure - Main Configuration
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
    sentry = {
      source  = "jianyuan/sentry"
      version = "~> 0.12.0"
    }
  }
}

# ============================================================================
# Provider Configuration
# ============================================================================

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth

  # Alternative: Use backend key instead of basic auth
  # backend_key = var.grafana_backend_key
}

provider "sentry" {
  token    = var.sentry_auth_token
  base_url = var.sentry_base_url  # Support for self-hosted Sentry
}

# ============================================================================
# Grafana Module - Datasources and Dashboards
# ============================================================================

module "grafana" {
  source = "./modules/grafana"

  # InfluxDB configuration
  influxdb_url      = var.influxdb_url
  influxdb_database = var.influxdb_database
  influxdb_username = var.influxdb_username
  influxdb_password = var.influxdb_password

  # Prometheus configuration
  prometheus_url                  = var.prometheus_url
  prometheus_basic_auth_user      = var.prometheus_basic_auth_user
  prometheus_basic_auth_password  = var.prometheus_basic_auth_password

  # Feature flags
  enable_influxdb   = var.enable_influxdb
  enable_prometheus = var.enable_prometheus

  # Default datasource
  influxdb_is_default   = var.influxdb_is_default
  prometheus_is_default = var.prometheus_is_default

  # Dashboard configuration
  enable_k6_dashboard                     = var.enable_k6_dashboard
  enable_node_exporter_dashboard          = var.enable_node_exporter_dashboard
  enable_cadvisor_dashboard               = var.enable_cadvisor_dashboard
  import_k6_official_dashboard            = var.import_k6_official_dashboard
  import_node_exporter_official_dashboard = var.import_node_exporter_official_dashboard

  # Alerting configuration
  enable_alerting         = var.enable_alerting
  alert_email_addresses   = var.alert_email_addresses
  alert_slack_webhook_url = var.alert_slack_webhook_url
  alert_webhook_url       = var.alert_webhook_url
}

# ============================================================================
# Sentry Module - Error Tracking
# ============================================================================

module "sentry" {
  source = "./modules/sentry"

  # Sentry instance configuration
  sentry_url        = var.sentry_url
  sentry_base_url   = var.sentry_base_url
  sentry_auth_token = var.sentry_auth_token

  # Organization
  sentry_organization = var.sentry_organization
  sentry_team         = var.sentry_team

  # Projects
  enable_backend_project  = var.enable_backend_sentry
  backend_project_name    = var.sentry_backend_project_name
  backend_project_slug    = var.sentry_backend_project_slug

  enable_frontend_project = var.enable_frontend_sentry
  frontend_project_name   = var.sentry_frontend_project_name
  frontend_project_slug   = var.sentry_frontend_project_slug

  # Alert rules
  enable_alert_rules = var.enable_sentry_alerts
  auto_resolve_age   = var.sentry_auto_resolve_age
}

# ============================================================================
# Future Modules (Uncomment when ready)
# ============================================================================

# module "datadog" {
#   source = "./modules/datadog"
#
#   datadog_backend_key = var.datadog_backend_key
#   datadog_app_key = var.datadog_app_key
# }

# module "pagerduty" {
#   source = "./modules/pagerduty"
#
#   pagerduty_token = var.pagerduty_token
# }
