# ============================================================================
# Sentry Module Outputs
# ============================================================================

# Backend Project Outputs
# ============================================================================

output "backend_project_id" {
  description = "Backend project ID"
  value       = try(sentry_project.backend[0].id, null)
}

output "backend_project_slug" {
  description = "Backend project slug"
  value       = try(sentry_project.backend[0].slug, null)
}

output "backend_project_url" {
  description = "Backend project URL"
  value       = try("${var.sentry_url}/organizations/${var.sentry_organization}/projects/${sentry_project.backend[0].slug}/", null)
}

output "backend_dsn_public" {
  description = "Backend project DSN (public)"
  value       = try(sentry_key.backend[0].dsn_public, null)
}

output "backend_dsn_secret" {
  description = "Backend project DSN (secret) - Keep this secure!"
  value       = try(sentry_key.backend[0].dsn_secret, null)
  sensitive   = true
}

output "backend_dsn_csp" {
  description = "Backend project DSN for Content Security Policy"
  value       = try(sentry_key.backend[0].dsn_csp, null)
}

# Frontend Project Outputs
# ============================================================================

output "frontend_project_id" {
  description = "Frontend project ID"
  value       = try(sentry_project.frontend[0].id, null)
}

output "frontend_project_slug" {
  description = "Frontend project slug"
  value       = try(sentry_project.frontend[0].slug, null)
}

output "frontend_project_url" {
  description = "Frontend project URL"
  value       = try("${var.sentry_url}/organizations/${var.sentry_organization}/projects/${sentry_project.frontend[0].slug}/", null)
}

output "frontend_dsn_public" {
  description = "Frontend project DSN (public)"
  value       = try(sentry_key.frontend[0].dsn_public, null)
}

output "frontend_dsn_secret" {
  description = "Frontend project DSN (secret) - Keep this secure!"
  value       = try(sentry_key.frontend[0].dsn_secret, null)
  sensitive   = true
}

output "frontend_dsn_csp" {
  description = "Frontend project DSN for Content Security Policy"
  value       = try(sentry_key.frontend[0].dsn_csp, null)
}

# Summary Outputs
# ============================================================================

output "projects_summary" {
  description = "Summary of created Sentry projects"
  value = {
    backend_enabled  = var.enable_backend_project
    frontend_enabled = var.enable_frontend_project
    organization     = var.sentry_organization
    team             = var.sentry_team
  }
}

output "backend_instructions" {
  description = "Instructions for using Sentry backend and viewing projects"
  value = <<-EOT

    📚 SENTRY PROJECTS CONFIGURED
    ════════════════════════════════════════════════════════════════════════

    ${var.enable_backend_project ? "✅ Backend Project: ${sentry_project.backend[0].name}" : "⏭️  Backend Project: Disabled"}
    ${var.enable_frontend_project ? "✅ Frontend Project: ${sentry_project.frontend[0].name}" : "⏭️  Frontend Project: Disabled"}

    ────────────────────────────────────────────────────────────────────────
    🔗 VIEW YOUR PROJECTS
    ────────────────────────────────────────────────────────────────────────

    ${var.enable_backend_project ? "Backend:  ${var.sentry_url}/organizations/${var.sentry_organization}/projects/${sentry_project.backend[0].slug}/" : ""}
    ${var.enable_frontend_project ? "Frontend: ${var.sentry_url}/organizations/${var.sentry_organization}/projects/${sentry_project.frontend[0].slug}/" : ""}

    ────────────────────────────────────────────────────────────────────────
    🔑 DSN KEYS (Data Source Names)
    ────────────────────────────────────────────────────────────────────────

    ${var.enable_backend_project ? "Backend DSN (Public):  ${sentry_key.backend[0].dsn_public}" : ""}
    ${var.enable_frontend_project ? "Frontend DSN (Public): ${sentry_key.frontend[0].dsn_public}" : ""}

    💡 Use these DSN values in your application environment variables:
       Backend:  SENTRY_DSN
       Frontend: NEXT_PUBLIC_SENTRY_DSN

    ⚠️  Secret DSNs are marked as sensitive. View with:
       terraform output -json | jq '.sentry.value.backend_dsn_secret.value'

    ────────────────────────────────────────────────────────────────────────
    🔗 SENTRY backend
    ────────────────────────────────────────────────────────────────────────

    Base URL: ${var.sentry_base_url}/backend/0/

    Example: List all projects
    curl -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
         ${var.sentry_base_url}/backend/0/organizations/${var.sentry_organization}/projects/

    📖 backend Documentation: https://docs.sentry.io/backend/

    ════════════════════════════════════════════════════════════════════════

  EOT
}
