# Supabase Module - Main Configuration

# Random password for Supabase database (only if creating project via Terraform)
resource "random_password" "supabase_db_password" {
  count   = var.create_project ? 1 : 0
  length  = 32
  special = true
}

# Supabase Project (only if creating via Terraform)
resource "supabase_project" "main" {
  count = var.create_project ? 1 : 0

  organization_id   = var.organization_id
  name              = var.project_name
  database_password = random_password.supabase_db_password[0].result
  region            = var.region

}

# Get backend keys for the project
data "supabase_apikeys" "main" {
  count       = var.create_project ? 1 : 0
  project_ref = supabase_project.main[0].id
}

# If using existing project, get backend keys
data "supabase_apikeys" "existing" {
  count       = var.create_project ? 0 : 1
  project_ref = var.existing_project_ref
}
