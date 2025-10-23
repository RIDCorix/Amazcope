# ============================================================================
# DevOps Infrastructure Outputs
# ============================================================================

# Grafana Module Outputs
# ============================================================================

output "grafana_url" {
  description = "URL of the Grafana instance"
  value       = var.grafana_url
}

output "grafana_influxdb_datasource_uid" {
  description = "UID of the InfluxDB datasource"
  value       = module.grafana.influxdb_datasource_uid
}

output "grafana_prometheus_datasource_uid" {
  description = "UID of the Prometheus datasource"
  value       = module.grafana.prometheus_datasource_uid
}

output "grafana_k6_dashboard_uid" {
  description = "UID of the k6 load testing dashboard"
  value       = module.grafana.k6_dashboard_uid
}

output "grafana_node_exporter_dashboard_uid" {
  description = "UID of the Node Exporter dashboard"
  value       = module.grafana.node_exporter_dashboard_uid
}

output "grafana_cadvisor_dashboard_uid" {
  description = "UID of the cAdvisor container metrics dashboard"
  value       = module.grafana.cadvisor_dashboard_uid
}

output "grafana_datasource_summary" {
  description = "Summary of Grafana datasources"
  value       = module.grafana.datasource_summary
}

output "grafana_dashboard_summary" {
  description = "Summary of Grafana dashboards"
  value       = module.grafana.dashboard_summary
}

output "grafana_alerting_summary" {
  description = "Summary of Grafana alert rules"
  value       = module.grafana.alerting_summary
  sensitive   = true
}

output "grafana_alert_rule_groups" {
  description = "List of configured alert rule groups"
  value       = module.grafana.alert_rule_groups
}

# Dashboard URLs
# ============================================================================

output "k6_dashboard_url" {
  description = "URL to access the k6 load testing dashboard"
  value       = var.enable_k6_dashboard && var.enable_influxdb ? "${var.grafana_url}/d/k6-load-testing/k6-load-testing-results" : null
}

output "node_exporter_dashboard_url" {
  description = "URL to access the Node Exporter dashboard"
  value       = var.enable_node_exporter_dashboard && var.enable_prometheus ? "${var.grafana_url}/d/node-exporter-full/node-exporter-full" : null
}

output "cadvisor_dashboard_url" {
  description = "URL to access the cAdvisor container metrics dashboard"
  value       = module.grafana.cadvisor_dashboard_url
}

# Usage Examples Output
# ============================================================================

output "usage_examples" {
  description = "Examples of how to use the infrastructure"
  value = <<-EOT

  ═══════════════════════════════════════════════════════════════════════════
  ✅ Amazcope DevOps Infrastructure Deployed Successfully!
  ═══════════════════════════════════════════════════════════════════════════

  📊 Grafana:
     URL: ${var.grafana_url}
     Dashboards:
       ${var.enable_k6_dashboard && var.enable_influxdb ? format("✅ k6: %s/d/k6-load-testing", var.grafana_url) : "⬜ k6 (disabled)"}
       ${var.enable_node_exporter_dashboard && var.enable_prometheus ? format("✅ Node Exporter: %s/d/node-exporter-full", var.grafana_url) : "⬜ Node Exporter (disabled)"}
       ${var.enable_cadvisor_dashboard && var.enable_prometheus ? format("✅ cAdvisor: %s/d/cadvisor-containers", var.grafana_url) : "⬜ cAdvisor (disabled)"}

  � Alerting:
     ${var.enable_alerting ? "✅ Enabled" : "⬜ Disabled"}
     ${var.enable_alerting ? format("Alert Rules: %s/alerting/list", var.grafana_url) : ""}
     ${var.enable_alerting && var.enable_cadvisor_dashboard ? "✅ Container Alerts (5 rules)" : ""}
     ${var.enable_alerting && var.enable_node_exporter_dashboard ? "✅ System Alerts (4 rules)" : ""}
     ${var.enable_alerting && var.enable_k6_dashboard ? "✅ Performance Alerts (2 rules)" : ""}
     ${var.enable_alerting ? format("Notifications: %d email(s)%s%s",
       length(var.alert_email_addresses),
       var.alert_slack_webhook_url != "" ? ", Slack" : "",
       var.alert_webhook_url != "" ? ", Webhook" : ""
     ) : ""}

  �🔧 Datasources:
     ${var.enable_influxdb ? format("✅ InfluxDB: %s", var.influxdb_url) : "⬜ InfluxDB (disabled)"}
     ${var.enable_prometheus ? format("✅ Prometheus: %s", var.prometheus_url) : "⬜ Prometheus (disabled)"}

  📈 Run k6 Test:
     cd load-tests/k6
     k6 run --out influxdb=${var.influxdb_url}/${var.influxdb_database} throughput-test.js

  ═══════════════════════════════════════════════════════════════════════════
  EOT
}

# ============================================================================
# Sentry Module Outputs
# ============================================================================

output "sentry_backend_project_id" {
  description = "Backend Sentry project ID"
  value       = module.sentry.backend_project_id
}

output "sentry_backend_project_slug" {
  description = "Backend Sentry project slug"
  value       = module.sentry.backend_project_slug
}

output "sentry_backend_project_url" {
  description = "Backend Sentry project URL"
  value       = module.sentry.backend_project_url
}

output "sentry_frontend_project_id" {
  description = "Frontend Sentry project ID"
  value       = module.sentry.frontend_project_id
}

output "sentry_frontend_project_slug" {
  description = "Frontend Sentry project slug"
  value       = module.sentry.frontend_project_slug
}

output "sentry_frontend_project_url" {
  description = "Frontend Sentry project URL"
  value       = module.sentry.frontend_project_url
}

output "sentry_backend_dsn_public" {
  description = "Backend Sentry DSN (public)"
  value       = module.sentry.backend_dsn_public
}

output "sentry_backend_dsn_secret" {
  description = "Backend Sentry DSN (secret) - Keep this secure!"
  value       = module.sentry.backend_dsn_secret
  sensitive   = true
}

output "sentry_frontend_dsn_public" {
  description = "Frontend Sentry DSN (public)"
  value       = module.sentry.frontend_dsn_public
}

output "sentry_frontend_dsn_secret" {
  description = "Frontend Sentry DSN (secret) - Keep this secure!"
  value       = module.sentry.frontend_dsn_secret
  sensitive   = true
}

output "sentry_projects_summary" {
  description = "Summary of Sentry projects"
  value       = module.sentry.projects_summary
}

output "sentry_backend_instructions" {
  description = "Instructions for getting DSN keys via backend"
  value       = module.sentry.backend_instructions
}

# ============================================================================
# Sentry Usage Examples
# ============================================================================

output "sentry_usage_examples" {
  description = "Examples of how to use Sentry in your applications"
  value = <<-EOT

  ═══════════════════════════════════════════════════════════════════════════
  🔔 Sentry Error Tracking Configured
  ═══════════════════════════════════════════════════════════════════════════

  📦 Projects:
     ${var.enable_backend_sentry ? format("✅ Backend: %s", var.sentry_backend_project_slug) : "⬜ Backend (disabled)"}
     ${var.enable_frontend_sentry ? format("✅ Frontend: %s", var.sentry_frontend_project_slug) : "⬜ Frontend (disabled)"}

  🔧 Configuration:
     Organization: ${var.sentry_organization}
     Team: ${var.sentry_team}

  🔑 DSN Keys:
     Backend DSN:  ${module.sentry.backend_dsn_public != null ? module.sentry.backend_dsn_public : "(disabled)"}
     Frontend DSN: ${module.sentry.frontend_dsn_public != null ? module.sentry.frontend_dsn_public : "(disabled)"}

     💡 View secret DSNs:
        terraform output sentry_backend_dsn_secret
        terraform output sentry_frontend_dsn_secret

  📝 Backend Integration (Fastbackend):
     # backend/.env
     SENTRY_DSN=${module.sentry.backend_dsn_public != null ? module.sentry.backend_dsn_public : "<your-backend-dsn>"}

     # backend/src/main.py
     import sentry_sdk
     from sentry_sdk.integrations.fastbackend import FastbackendIntegration

     sentry_sdk.init(
         dsn=settings.SENTRY_DSN,
         integrations=[FastbackendIntegration()],
         environment="${terraform.workspace}",
         traces_sample_rate=1.0,
     )

  📝 Frontend Integration (Next.js):
     # frontend/.env.local
     NEXT_PUBLIC_SENTRY_DSN=${module.sentry.frontend_dsn_public != null ? module.sentry.frontend_dsn_public : "<your-frontend-dsn>"}

     # frontend/sentry.config.ts
     import * as Sentry from "@sentry/nextjs";

     Sentry.init({
         dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
         environment: process.env.NODE_ENV,
         tracesSampleRate: 1.0,
     });

  🌐 View in Sentry:
     https://sentry.io/organizations/${var.sentry_organization}/projects/

  ═══════════════════════════════════════════════════════════════════════════
  EOT
}
