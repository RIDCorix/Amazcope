# ============================================================================
# Sentry Module - Error Tracking and Monitoring
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    sentry = {
      source  = "jianyuan/sentry"
      version = "~> 0.12.0"
    }
  }
}

# ============================================================================
# Configure Sentry Provider
# ============================================================================
#
# SELF-HOSTED SENTRY:
#   Get your auth token from: http://localhost:9000/settings/account/security/
#   Or via CLI: docker exec -it sentry sentry createtoken
#   Or create via backend:
#     docker exec -it sentry sentry createuser --email=admin@example.com --superuser
#     docker exec -it sentry sentry createtoken
#
# SAAS SENTRY:
#   Get your auth token from: https://sentry.io/settings/account/backend/auth-tokens/
#
# Required scopes: project:read, project:write, project:admin, org:read
# ============================================================================

provider "sentry" {
  token    = var.sentry_auth_token
  base_url = var.sentry_base_url  # Support for self-hosted Sentry
}

# ============================================================================
# Sentry Project
# ============================================================================

resource "sentry_project" "backend" {
  count = var.enable_backend_project ? 1 : 0

  organization = var.sentry_organization
  teams        = [var.sentry_team]
  name         = var.backend_project_name
  slug         = var.backend_project_slug
  platform     = "python-fastbackend"

  resolve_age = var.auto_resolve_age
}

resource "sentry_project" "frontend" {
  count = var.enable_frontend_project ? 1 : 0

  organization = var.sentry_organization
  teams        = [var.sentry_team]
  name         = var.frontend_project_name
  slug         = var.frontend_project_slug
  platform     = "javascript-nextjs"

  resolve_age = var.auto_resolve_age
}

# ============================================================================
# Client Keys (DSN)
# ============================================================================

resource "sentry_key" "backend" {
  count = var.enable_backend_project ? 1 : 0

  organization = var.sentry_organization
  project      = sentry_project.backend[0].slug
  name         = "Default"
}

resource "sentry_key" "frontend" {
  count = var.enable_frontend_project ? 1 : 0

  organization = var.sentry_organization
  project      = sentry_project.frontend[0].slug
  name         = "Default"
}

# ============================================================================
# Alert Rules
# ============================================================================

# Note: Alert rules (sentry_rule resource) are not supported by the current
# Sentry Terraform provider (v0.12.x). Alert rules should be configured
# manually in the Sentry dashboard or via Sentry backend.
#
# To create alert rules:
# 1. Go to https://sentry.io/organizations/YOUR_ORG/projects/
# 2. Select project → Alerts → Create Alert
# 3. Configure conditions (e.g., error spike > 100 events in 5 minutes)
# 4. Set actions (email, Slack, webhook, etc.)
#
# Example backend call for creating alert rules (use after Terraform apply):
# curl -X POST https://sentry.io/backend/0/projects/ORG/PROJECT/rules/ \
#   -H "Authorization: Bearer $SENTRY_TOKEN" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "name": "Error Spike Alert",
#     "conditions": [...],
#     "actions": [...]
#   }'

# ============================================================================
# Environment Tags (Optional)
# ============================================================================

# Note: Environments are created automatically when events are sent
# This is just documentation of expected environments
locals {
  environments = ["production", "staging", "development"]
}
