# ============================================================================
# Grafana Module Outputs
# ============================================================================

# InfluxDB Datasource Outputs
# ============================================================================

output "influxdb_datasource_uid" {
  description = "UID of the InfluxDB datasource (for k6 metrics)"
  value       = try(grafana_data_source.influxdb[0].uid, null)
}

output "influxdb_datasource_name" {
  description = "Name of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].name, null)
}

output "influxdb_datasource_url" {
  description = "URL of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].url, null)
}

output "influxdb_datasource_id" {
  description = "Internal ID of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].id, null)
}

# Prometheus Datasource Outputs
# ============================================================================

output "prometheus_datasource_uid" {
  description = "UID of the Prometheus datasource (for application metrics)"
  value       = try(grafana_data_source.prometheus[0].uid, null)
}

output "prometheus_datasource_name" {
  description = "Name of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].name, null)
}

output "prometheus_datasource_url" {
  description = "URL of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].url, null)
}

output "prometheus_datasource_id" {
  description = "Internal ID of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].id, null)
}

# Dashboard Outputs
# ============================================================================

output "k6_dashboard_uid" {
  description = "UID of the k6 load testing dashboard"
  value       = try(grafana_dashboard.k6_load_testing[0].uid, null)
}

output "node_exporter_dashboard_uid" {
  description = "UID of the Node Exporter dashboard"
  value       = try(grafana_dashboard.node_exporter[0].uid, null)
}

output "cadvisor_dashboard_uid" {
  description = "UID of the cAdvisor container metrics dashboard"
  value       = try(grafana_dashboard.cadvisor[0].uid, null)
}

output "cadvisor_dashboard_url" {
  description = "URL to access the cAdvisor Container Metrics dashboard"
  value       = var.enable_cadvisor_dashboard && var.enable_prometheus ? "http://localhost:3005/d/cadvisor-containers/cadvisor-container-metrics" : null
}

# Summary Outputs
# ============================================================================

output "datasource_summary" {
  description = "Summary of configured datasources"
  value = {
    influxdb_enabled   = var.enable_influxdb
    prometheus_enabled = var.enable_prometheus
    default_datasource = var.influxdb_is_default ? "InfluxDB-k6" : (var.prometheus_is_default ? "Prometheus" : "none")
  }
}

output "dashboard_summary" {
  description = "Summary of created dashboards"
  value = {
    k6_dashboard_enabled            = var.enable_k6_dashboard && var.enable_influxdb
    node_exporter_dashboard_enabled = var.enable_node_exporter_dashboard && var.enable_prometheus
    cadvisor_dashboard_enabled      = var.enable_cadvisor_dashboard && var.enable_prometheus
  }
}

# ============================================================================
# Alert Rule Outputs
# ============================================================================

output "alerting_summary" {
  description = "Summary of configured alert rules"
  value = {
    alerting_enabled           = var.enable_alerting
    container_alerts_enabled   = var.enable_prometheus && var.enable_cadvisor_dashboard && var.enable_alerting
    system_alerts_enabled      = var.enable_prometheus && var.enable_node_exporter_dashboard && var.enable_alerting
    performance_alerts_enabled = var.enable_influxdb && var.enable_k6_dashboard && var.enable_alerting
    email_notifications        = var.enable_alerting ? length(var.alert_email_addresses) : 0
    slack_enabled              = var.enable_alerting && var.alert_slack_webhook_url != ""
    webhook_enabled            = var.enable_alerting && var.alert_webhook_url != ""
  }
}

output "alert_rule_groups" {
  description = "List of created alert rule groups"
  value = var.enable_alerting ? [
    var.enable_prometheus && var.enable_cadvisor_dashboard ? "Container Alerts" : null,
    var.enable_prometheus && var.enable_node_exporter_dashboard ? "System Alerts" : null,
    var.enable_influxdb && var.enable_k6_dashboard ? "Performance Alerts" : null,
  ] : []
}
