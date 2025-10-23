# ============================================================================
# Terraform Outputs - Datasource Information
# ============================================================================

# Output datasource UIDs for use in dashboard JSON imports
# These UIDs are used to reference datasources in dashboard definitions

# ============================================================================
# InfluxDB Datasource Outputs
# ============================================================================

output "influxdb_datasource_uid" {
  description = "UID of the InfluxDB datasource (for k6 metrics)"
  value       = try(grafana_data_source.influxdb[0].uid, null)
  sensitive   = false
}

output "influxdb_datasource_name" {
  description = "Name of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].name, null)
  sensitive   = false
}

output "influxdb_datasource_url" {
  description = "URL of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].url, null)
  sensitive   = false
}

output "influxdb_datasource_id" {
  description = "Internal ID of the InfluxDB datasource"
  value       = try(grafana_data_source.influxdb[0].id, null)
  sensitive   = false
}

# ============================================================================
# Prometheus Datasource Outputs
# ============================================================================

output "prometheus_datasource_uid" {
  description = "UID of the Prometheus datasource (for application metrics)"
  value       = try(grafana_data_source.prometheus[0].uid, null)
  sensitive   = false
}

output "prometheus_datasource_name" {
  description = "Name of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].name, null)
  sensitive   = false
}

output "prometheus_datasource_url" {
  description = "URL of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].url, null)
  sensitive   = false
}

output "prometheus_datasource_id" {
  description = "Internal ID of the Prometheus datasource"
  value       = try(grafana_data_source.prometheus[0].id, null)
  sensitive   = false
}

# ============================================================================
# Sentry Datasource Outputs
# ============================================================================

output "sentry_datasource_uid" {
  description = "UID of the Sentry datasource (for error tracking)"
  value       = try(grafana_data_source.sentry[0].uid, null)
  sensitive   = false
}

output "sentry_datasource_name" {
  description = "Name of the Sentry datasource"
  value       = try(grafana_data_source.sentry[0].name, null)
  sensitive   = false
}

output "sentry_datasource_url" {
  description = "URL of the Sentry datasource"
  value       = try(grafana_data_source.sentry[0].url, null)
  sensitive   = false
}

output "sentry_datasource_id" {
  description = "Internal ID of the Sentry datasource"
  value       = try(grafana_data_source.sentry[0].id, null)
  sensitive   = false
}

# ============================================================================
# Grafana Configuration Outputs
# ============================================================================

output "grafana_url" {
  description = "URL of the Grafana instance"
  value       = var.grafana_url
  sensitive   = false
}

output "datasource_configuration_summary" {
  description = "Summary of configured datasources"
  value = {
    influxdb_enabled   = var.enable_influxdb
    prometheus_enabled = var.enable_prometheus
    sentry_enabled     = var.enable_sentry
    default_datasource = var.influxdb_is_default ? "InfluxDB-k6" : (var.prometheus_is_default ? "Prometheus" : "none")
  }
  sensitive = false
}

# ============================================================================
# Dashboard Outputs
# ============================================================================

output "k6_dashboard_uid" {
  description = "UID of the k6 load testing dashboard"
  value       = try(grafana_dashboard.k6[0].uid, null)
  sensitive   = false
}

output "k6_dashboard_url" {
  description = "URL to access the k6 load testing dashboard"
  value       = var.enable_k6_dashboard && var.enable_influxdb ? "${var.grafana_url}/d/k6-load-testing/k6-load-testing-results" : null
  sensitive   = false
}

output "node_exporter_dashboard_uid" {
  description = "UID of the Node Exporter dashboard"
  value       = try(grafana_dashboard.node_exporter[0].uid, null)
  sensitive   = false
}

output "cadvisor_dashboard_uid" {
  description = "UID of the cAdvisor Container Metrics dashboard"
  value       = try(grafana_dashboard.cadvisor[0].uid, null)
  sensitive   = false
}

output "cadvisor_dashboard_url" {
  description = "URL to access the cAdvisor Container Metrics dashboard"
  value       = var.enable_cadvisor_dashboard && var.enable_prometheus ? "${var.grafana_url}/d/cadvisor-containers/cadvisor-container-metrics" : null
  sensitive   = false
}

output "sentry_dashboard_url" {
  description = "URL to access the Sentry Error Tracking dashboard"
  value       = var.enable_sentry_dashboard && var.enable_sentry ? "${var.grafana_url}/d/sentry-errors/sentry-error-tracking" : null
  sensitive   = false
}

output "dashboard_summary" {
  description = "Summary of created dashboards"
  value = {
    k6_dashboard_enabled       = var.enable_k6_dashboard && var.enable_influxdb
    cadvisor_dashboard_enabled = var.enable_cadvisor_dashboard && var.enable_prometheus
    sentry_dashboard_enabled   = var.enable_sentry_dashboard && var.enable_sentry
  }
  sensitive = false
}

# ============================================================================
# Usage Examples (printed after terraform apply)
# ============================================================================

output "usage_examples" {
  description = "Examples of how to use the datasource UIDs"
  value = <<-EOT

  ═══════════════════════════════════════════════════════════════════════════
  ✅ Grafana Datasources Created Successfully!
  ═══════════════════════════════════════════════════════════════════════════

  📊 Access Grafana:
     ${var.grafana_url}

  🔌 Configured Datasources:
     ${var.enable_influxdb ? "✅ InfluxDB-k6 (for k6 load testing metrics)" : "⬜ InfluxDB (disabled)"}
     ${var.enable_prometheus ? "✅ Prometheus (for application & container metrics)" : "⬜ Prometheus (disabled)"}
     ${var.enable_sentry ? "✅ Sentry (for error tracking)" : "⬜ Sentry (disabled)"}

  🎯 Default Datasource:
     ${var.influxdb_is_default ? "InfluxDB-k6" : (var.prometheus_is_default ? "Prometheus" : "None")}

  📈 Dashboards Created:
     ${var.enable_k6_dashboard && var.enable_influxdb ? format("✅ k6 Load Testing: %s/d/k6-load-testing", var.grafana_url) : "⬜ k6 Dashboard (disabled)"}
     ${var.enable_cadvisor_dashboard && var.enable_prometheus ? format("✅ cAdvisor Containers: %s/d/cadvisor-containers", var.grafana_url) : "⬜ cAdvisor Dashboard (disabled)"}
     ${var.enable_sentry_dashboard && var.enable_sentry ? format("✅ Sentry Errors: %s/d/sentry-errors", var.grafana_url) : "⬜ Sentry Dashboard (disabled)"}

  💡 Alternative: Import Official Dashboards from grafana.com
     k6 (ID: 2587): ${var.grafana_url}/dashboard/import
     cAdvisor (ID: 14282): ${var.grafana_url}/dashboard/import

  🔧 Datasource UIDs (for backend/JSON usage):
     ${var.enable_influxdb ? format("InfluxDB:   %s", try(grafana_data_source.influxdb[0].uid, "N/A")) : "InfluxDB:   (disabled)"}
     ${var.enable_prometheus ? format("Prometheus: %s", try(grafana_data_source.prometheus[0].uid, "N/A")) : "Prometheus: (disabled)"}
     ${var.enable_sentry ? format("Sentry:     %s", try(grafana_data_source.sentry[0].uid, "N/A")) : "Sentry:     (disabled)"}

  📝 Example: Use UID in Dashboard JSON:
     {
       "datasource": {
         "type": "influxdb",
         "uid": "${try(grafana_data_source.influxdb[0].uid, "YOUR_INFLUXDB_UID")}"
       }
     }

  🧪 Test InfluxDB Connection:
     curl -G '${var.influxdb_url}/query' \
       --data-urlencode "db=${var.influxdb_database}" \
       --data-urlencode "q=SHOW MEASUREMENTS"

  🧪 Test Prometheus Connection:
     curl '${var.prometheus_url}/backend/v1/label/__name__/values'

  ═══════════════════════════════════════════════════════════════════════════
  EOT
  sensitive = false
}
