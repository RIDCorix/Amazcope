# Supabase Module Outputs

# Project Information
output "project_id" {
  description = "Supabase project ID"
  value       = var.create_project && length(supabase_project.main) > 0 ? supabase_project.main[0].id : var.manual_config.project_id
}

output "project_name" {
  description = "Supabase project name"
  value       = var.create_project && length(supabase_project.main) > 0 ? supabase_project.main[0].name : var.project_name
}

output "region" {
  description = "Supabase project region"
  value       = var.create_project && length(supabase_project.main) > 0 ? supabase_project.main[0].region : var.region
}

# Connection Information
output "backend_url" {
  description = "Supabase backend URL"
  value = var.create_project && length(supabase_project.main) > 0 ? (
    "https://${supabase_project.main[0].id}.supabase.co"
  ) : var.manual_config.url
}

output "database_url" {
  description = "Database connection URL"
  value = var.create_project && length(supabase_project.main) > 0 ? (
    "postgresql://postgres:${random_password.supabase_db_password[0].result}@${supabase_project.main[0].id}.supabase.co:5432/postgres"
  ) : var.manual_config.database_url
  sensitive = true
}

output "host" {
  description = "Database host"
  value = var.create_project && length(supabase_project.main) > 0 ? (
    "${supabase_project.main[0].id}.supabase.co"
  ) : var.manual_config.host
}

output "port" {
  description = "Database port"
  value       = 5432
}

output "database_name" {
  description = "Database name"
  value       = "postgres"
}

output "user" {
  description = "Database username"
  value       = "postgres"
}

output "password" {
  description = "Database password"
  value = var.create_project && length(random_password.supabase_db_password) > 0 ? (
    random_password.supabase_db_password[0].result
  ) : var.manual_config.password
  sensitive = true
}

# Authentication Keys
output "anon_key" {
  description = "Supabase anonymous key"
  value = var.create_project ? (
    length(data.supabase_apikeys.main) > 0 ? data.supabase_apikeys.main[0].anon_key : null
    ) : (
    length(data.supabase_apikeys.existing) > 0 ? data.supabase_apikeys.existing[0].anon_key : var.manual_config.anon_key
  )
  sensitive = true
}

output "service_role_key" {
  description = "Supabase service role key"
  value = var.create_project ? (
    length(data.supabase_apikeys.main) > 0 ? data.supabase_apikeys.main[0].service_role_key : null
    ) : (
    length(data.supabase_apikeys.existing) > 0 ? data.supabase_apikeys.existing[0].service_role_key : var.manual_config.service_role_key
  )
  sensitive = true
}

# Dashboard and Management
output "dashboard_url" {
  description = "Supabase dashboard URL"
  value = var.create_project && length(supabase_project.main) > 0 ? (
    "https://app.supabase.com/project/${supabase_project.main[0].id}"
    ) : (
    var.manual_config.project_id != "" ? "https://app.supabase.com/project/${var.manual_config.project_id}" : null
  )
}

# Status Information
output "created_via_terraform" {
  description = "Whether the project was created via Terraform"
  value       = var.create_project
}

output "project_exists" {
  description = "Whether the Supabase project exists (created or manual)"
  value = var.create_project ? length(supabase_project.main) > 0 : (
    var.manual_config.project_id != "" && var.manual_config.url != ""
  )
}
