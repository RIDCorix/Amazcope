# Supabase Terraform Module

This module manages Supabase projects and configurations through Terraform.

## Features

- 🏗️ **Project Management**: Create and configure Supabase projects
- 🔧 **Settings Configuration**: API, Auth, and Database settings
- 🗄️ **Database Setup**: Initial schema and migration support
- 🔑 **Credential Management**: Automatic key generation and retrieval
- 🎛️ **Flexible Configuration**: Support for both new and existing projects

## Usage

### Basic Usage - New Project

```hcl
module "supabase" {
  source = "./modules/supabase"

  create_project   = true
  organization_id  = "your-org-id"
  project_name     = "my-app-prod"
  region          = "us-east-1"

  tags = {
    Environment = "production"
    Project     = "my-app"
  }
}
```

### Advanced Usage - Custom Configuration

```hcl
module "supabase" {
  source = "./modules/supabase"

  create_project   = true
  organization_id  = "your-org-id"
  project_name     = "my-app-prod"
  region          = "us-east-1"
  plan            = "pro"

  # Custom API settings
  api_settings = {
    db_schema            = "public"
    db_extra_search_path = "public,extensions"
    max_rows             = 5000
  }

  # Custom Auth settings
  auth_settings = {
    enable_signup                      = true
    enable_anonymous_sign_ins          = false
    jwt_expiry                        = 7200
    refresh_token_rotation_enabled    = true
    security_refresh_token_reuse_interval = 10
    enable_confirmations              = true
    enable_recoveries                 = true
    password_min_length               = 12
  }

  # Database migrations
  run_database_migrations = true
  migration_sql = <<EOF
BEGIN
  -- Create application tables
  CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    price DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Create indexes
  CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);

  RETURN 'Application migrations completed';
END;
EOF

  tags = {
    Environment = "production"
    Project     = "my-app"
  }
}
```

### Existing Project Configuration

```hcl
module "supabase" {
  source = "./modules/supabase"

  create_project = false

  manual_config = {
    project_id       = "your-existing-project-id"
    url              = "https://your-project.supabase.co"
    anon_key         = "your-anon-key"
    service_role_key = "your-service-role-key"
    database_url     = "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
    host             = "db.your-project.supabase.co"
    user             = "postgres"
    password         = "your-password"
  }

  tags = {
    Environment = "production"
    Project     = "my-app"
  }
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| create_project | Whether to create a new Supabase project | `bool` | `true` | no |
| organization_id | Supabase organization ID | `string` | n/a | yes |
| project_name | Name of the Supabase project | `string` | n/a | yes |
| region | Supabase region | `string` | `"us-east-1"` | no |
| plan | Supabase plan (free, pro, team, enterprise) | `string` | `"free"` | no |
| kps_enabled | Enable Key Performance Statistics | `bool` | `false` | no |
| configure_settings | Whether to configure Supabase settings | `bool` | `true` | no |
| api_settings | API settings for Supabase | `object` | See variables.tf | no |
| auth_settings | Auth settings for Supabase | `object` | See variables.tf | no |
| db_settings | Database settings for Supabase | `object` | See variables.tf | no |
| create_database_schema | Whether to create initial database schema | `bool` | `true` | no |
| run_database_migrations | Whether to run database migrations | `bool` | `false` | no |
| migration_sql | SQL code for database migrations | `string` | Basic example | no |
| manual_config | Manual configuration for existing projects | `object` | Empty object | no |
| tags | Tags to apply to resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|:---------:|
| project_id | Supabase project ID | no |
| project_name | Supabase project name | no |
| region | Supabase project region | no |
| api_url | Supabase API URL | no |
| database_url | Database connection URL | yes |
| host | Database host | no |
| port | Database port | no |
| database_name | Database name | no |
| user | Database username | no |
| password | Database password | yes |
| anon_key | Supabase anonymous key | yes |
| service_role_key | Supabase service role key | yes |
| dashboard_url | Supabase dashboard URL | no |
| created_via_terraform | Whether project was created via Terraform | no |
| project_exists | Whether the Supabase project exists | no |

## Provider Configuration

This module requires the Supabase provider to be configured at the root level:

```hcl
# In your root main.tf
terraform {
  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }
}

provider "supabase" {
  access_token = var.supabase_access_token
}
```

## Getting Supabase Credentials

1. **Access Token**:
   - Go to https://app.supabase.com/account/tokens
   - Generate a new access token
   - Use this as `var.supabase_access_token`

2. **Organization ID**:
   - Go to your Supabase dashboard
   - The org ID is in the URL: `https://app.supabase.com/org/[org-id]`

## Examples

### Integration with AWS Secrets Manager

```hcl
module "supabase" {
  source = "./modules/supabase"

  create_project  = true
  organization_id = var.supabase_org_id
  project_name    = "${var.project_name}-${var.environment}"
  region         = var.supabase_region
}

resource "aws_secretsmanager_secret_version" "supabase" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    SUPABASE_URL              = module.supabase.api_url
    SUPABASE_ANON_KEY         = module.supabase.anon_key
    SUPABASE_SERVICE_ROLE_KEY = module.supabase.service_role_key
    DATABASE_URL              = module.supabase.database_url
    POSTGRES_HOST             = module.supabase.host
    POSTGRES_USER             = module.supabase.user
    POSTGRES_PASSWORD         = module.supabase.password
  })
}
```

### Conditional Module Usage

```hcl
module "supabase" {
  count  = var.use_supabase ? 1 : 0
  source = "./modules/supabase"

  create_project  = var.supabase_access_token != ""
  organization_id = var.supabase_org_id
  project_name    = "${var.project_name}-${var.environment}"

  # Use manual config if no access token provided
  manual_config = var.supabase_access_token == "" ? {
    project_id       = var.supabase_project_id
    url              = var.supabase_url
    anon_key         = var.supabase_anon_key
    service_role_key = var.supabase_service_role_key
    database_url     = var.supabase_database_url
    host             = var.supabase_host
    user             = var.supabase_user
    password         = var.supabase_password
  } : {}
}
```

## Requirements

- Terraform >= 1.0
- Supabase provider ~> 1.0
- Valid Supabase account and access token (for new projects)

## License

This module is part of the Amazcope project.
