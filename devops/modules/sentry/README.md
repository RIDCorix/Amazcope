# Sentry Terraform Module

This module creates Sentry projects for error tracking and monitoring.

## Features

- **Backend Project**: FastAPI error tracking
- **Frontend Project**: Next.js error tracking
- **Alert Rules**: Automated error spike detection
- **Auto-resolve**: Automatic issue resolution after inactivity
- **Rate Limiting**: Optional event rate limiting

## Usage

```hcl
module "sentry" {
  source = "./modules/sentry"

  # Organization
  sentry_organization = "amazcope"
  sentry_team         = "engineering"

  # Projects
  enable_backend_project  = true
  enable_frontend_project = true

  # Alert rules
  enable_alert_rules = true
  auto_resolve_age   = 24  # hours
}
```

## Provider Configuration

Add to root `main.tf`:

```hcl
provider "sentry" {
  token = var.sentry_auth_token
}
```

Get your Sentry auth token from:
https://sentry.io/settings/account/api/auth-tokens/

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| sentry_organization | Sentry organization slug | `string` | `"amazcope"` | no |
| sentry_team | Sentry team slug | `string` | `"engineering"` | no |
| enable_backend_project | Enable backend project | `bool` | `true` | no |
| backend_project_name | Backend project name | `string` | `"Amazcope  Backend"` | no |
| backend_project_slug | Backend project slug | `string` | `"amazcope-backend"` | no |
| enable_frontend_project | Enable frontend project | `bool` | `true` | no |
| frontend_project_name | Frontend project name | `string` | `"Amazcope  Frontend"` | no |
| frontend_project_slug | Frontend project slug | `string` | `"amazcope-frontend"` | no |
| enable_alert_rules | Enable alert rules | `bool` | `true` | no |
| auto_resolve_age | Auto-resolve after N hours | `number` | `0` (disabled) | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| backend_project_id | Backend project ID | No |
| backend_dsn | Backend DSN | Yes |
| backend_dsn_public | Backend public DSN | No |
| frontend_project_id | Frontend project ID | No |
| frontend_dsn | Frontend DSN | Yes |
| frontend_dsn_public | Frontend public DSN | No |
| projects_summary | Summary of projects | No |
| alert_rules_summary | Summary of alerts | No |

## Resources Created

- `sentry_project.backend` - Backend FastAPI project
- `sentry_project.frontend` - Frontend Next.js project
- `sentry_rule.backend_error_spike` - Backend error spike alert
- `sentry_rule.frontend_error_spike` - Frontend error spike alert

## Requirements

- Terraform >= 1.0
- Sentry provider ~> 0.12.0
- Sentry account with organization and team created

## Example with All Options

```hcl
module "sentry" {
  source = "./modules/sentry"

  # Organization
  sentry_organization = "my-org"
  sentry_team         = "backend-team"

  # Backend project
  enable_backend_project  = true
  backend_project_name    = "My Backend"
  backend_project_slug    = "my-backend"

  # Frontend project
  enable_frontend_project = true
  frontend_project_name   = "My Frontend"
  frontend_project_slug   = "my-frontend"

  # Alerts
  enable_alert_rules = true
  auto_resolve_age   = 72  # 3 days

  # Rate limiting
  rate_limit_backend  = 1000  # events per minute
  rate_limit_frontend = 5000
}
```

## Integration with Application

### Backend (FastAPI)

```python
# backend/src/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Get DSN from Terraform output
SENTRY_DSN = os.getenv("SENTRY_DSN")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FastApiIntegration()],
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=1.0,
)

app = FastAPI()
```

Get DSN:
```bash
terraform output -raw sentry_backend_dsn
```

### Frontend (Next.js)

```typescript
// frontend/src/sentry.config.ts
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

Get DSN:
```bash
terraform output -raw sentry_frontend_dsn
```

## Alert Rules

### Error Spike Detection

Triggers when:
- More than 100 errors in 5 minutes
- Sends email to issue owners
- Checks every 30 minutes

Customize in `main.tf`:
```hcl
conditions = jsonencode([
  {
    id = "sentry.rules.conditions.event_frequency.EventFrequencyCondition"
    interval = "5m"
    value = 100  # Change threshold here
  }
])
```

## Testing

```bash
# Initialize module
terraform init

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply configuration
terraform apply
```

## Verify in Sentry

After applying:

1. Go to https://sentry.io/organizations/your-org/projects/
2. Find "Amazcope  Backend" and "Amazcope  Frontend" projects
3. Click project → Settings → Client Keys (DSN)
4. Verify DSN matches Terraform output

## Troubleshooting

### Provider Authentication Failed

```bash
# Check token
echo $TF_VAR_sentry_auth_token

# Or set in terraform.tfvars
sentry_auth_token = "your-token-here"
```

### Organization or Team Not Found

```bash
# List organizations
curl -H "Authorization: Bearer $SENTRY_TOKEN" \
  https://sentry.io/api/0/organizations/

# List teams
curl -H "Authorization: Bearer $SENTRY_TOKEN" \
  https://sentry.io/api/0/organizations/your-org/teams/
```

### Project Already Exists

```bash
# Import existing project
terraform import module.sentry.sentry_project.backend[0] your-org/project-slug
```

## Environment Variables

For CI/CD:

```bash
export TF_VAR_sentry_auth_token="your-token"
export TF_VAR_sentry_organization="your-org"
export TF_VAR_sentry_team="your-team"
```

## Documentation

- **Sentry Provider**: https://registry.terraform.io/providers/jianyuan/sentry/latest/docs
- **Sentry API**: https://docs.sentry.io/api/
- **Alert Rules**: https://docs.sentry.io/product/alerts-notifications/alerts/
