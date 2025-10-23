# Terraform AWS Infrastructure for Amazcope

This Terraform configuration deploys the complete Amazcope infrastructure on AWS with support for **external PostgreSQL databases** (Supabase, AWS RDS, or any PostgreSQL provider).

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Infrastructure                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐ │
│  │     VPC     │    │     ALB      │    │    ECS Fargate      │ │
│  │             │    │              │    │                     │ │
│  │ Public      │    │ Load         │    │ ┌─────────────────┐ │ │
│  │ Subnets     │◄───┤ Balancer     │◄───┤ │   API Tasks     │ │ │
│  │             │    │              │    │ └─────────────────┘ │ │
│  │ Private     │    │              │    │ ┌─────────────────┐ │ │
│  │ Subnets     │    │              │    │ │ Worker Tasks    │ │ │
│  │             │    │              │    │ └─────────────────┘ │ │
│  └─────────────┘    └──────────────┘    └─────────────────────┘ │
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐ │
│  │  PostgreSQL │    │    Redis     │    │   Secrets Manager   │ │
│  │  (External) │    │ ElastiCache  │    │                     │ │
│  │             │    │              │    │ - Database Creds    │ │
│  │ Your DB     │    │              │    │ - API Keys          │ │
│  │ Provider    │    │              │    │ - JWT Secrets       │ │
│  └─────────────┘    └──────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🗄️ Database Configuration

This Terraform setup now uses **direct PostgreSQL credentials** that you provide. You can use any PostgreSQL database provider:

### Supported Database Providers

**1. Supabase (Recommended)**
- ✅ Modern PostgreSQL with built-in features (Auth, Real-time, Storage)
- ✅ Automatic backups and point-in-time recovery
- ✅ Built-in dashboard for database management
- ✅ Generous free tier with auto-scaling
- ✅ Global CDN and edge computing

**2. AWS RDS PostgreSQL**
- ✅ Full AWS integration and compliance
- ✅ VPC-native security (private subnets)
- ✅ Multi-AZ high availability options
- ✅ Custom backup and maintenance windows

**3. Other Providers**
- Railway, Neon, DigitalOcean Managed Databases, Render, etc.
- Any PostgreSQL instance accessible from AWS

### Configuration

Simply provide your database credentials in `terraform.tfvars`:

```hcl
postgres_host     = "db.your-project.supabase.co"
postgres_port     = "5432"
postgres_db       = "postgres"
postgres_user     = "postgres"
postgres_password = "your-secure-password"
```

## 💰 AWS Free Tier Option

For users on AWS free tier or wanting to minimize costs, you can deploy **without Application Load Balancer** to save ~$22/month:

```hcl
# In terraform.tfvars
enable_alb = false  # Disables ALB, uses direct ECS access
```

**Benefits:**
- ✅ Eliminates ALB costs (~$22/month → $0)
- ✅ Still fully functional API access
- ✅ Compatible with AWS free tier limits
- ✅ Easy upgrade path to ALB when ready

**Trade-offs:**
- ⚠️ No load balancing (single point of failure)
- ⚠️ No SSL termination (HTTP only)
- ⚠️ Manual service discovery via ECS task IPs

📖 **Full Guide:** See [FREE_TIER_GUIDE.md](./FREE_TIER_GUIDE.md) for complete setup instructions, access methods, and upgrade paths.

## 🌐 Frontend Hosting

**CloudFront + S3 Static Hosting** for the Next.js frontend:

**Features:**
- ✅ Global CDN with edge caching
- ✅ SSL/TLS termination
- ✅ Custom domain support
- ✅ Optimized cache strategies
- ✅ SPA routing support
- ✅ Cost-effective (starts at ~$1/month)

**Quick Deploy:**
```bash
# Deploy infrastructure
terraform apply

# Deploy frontend
./deploy-frontend.sh
```

� **Full Guide:** See [FRONTEND_HOSTING.md](./FRONTEND_HOSTING.md) for complete frontend deployment instructions.

## �🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** 1.5+ installed
3. **Supabase account** (if using Supabase option)

### Module Structure

The infrastructure uses a modular approach:

```
deployment/aws/
├── main.tf                    # Root configuration and provider setup
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── ecs.tf                    # ECS services and tasks
├── vpc.tf                    # VPC and networking
├── alb.tf                    # Application Load Balancer
├── elasticache.tf            # Redis configuration
├── monitoring.tf             # CloudWatch and alerting
└── modules/
    ├── supabase/             # Supabase module
    │   ├── main.tf          # Supabase resources
    │   ├── variables.tf     # Module variables
    │   ├── outputs.tf       # Module outputs
    │   ├── versions.tf      # Provider requirements
    │   └── README.md        # Module documentation
    ├── rds/                 # RDS module (if needed)
    ├── vpc/                 # VPC module (if needed)
    └── redis/               # Redis module (if needed)
```

### Step 1: Configure Variables

```bash
# Copy the example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit the configuration
vim terraform.tfvars
```

### Step 2: Choose Database Option

#### Option A: Supabase (Terraform-Managed)

```hcl
# In terraform.tfvars
use_supabase = true
supabase_access_token = "sbp_your-token-here"  # Get from https://app.supabase.com/account/tokens
supabase_org_id = "your-org-id"               # Get from dashboard URL
```

**Getting Supabase Credentials:**
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create account or log in
3. Generate access token: https://app.supabase.com/account/tokens
4. Find org ID in dashboard URL: `https://app.supabase.com/org/[org-id]`

#### Option B: Supabase (Existing Project)

```hcl
# In terraform.tfvars
use_supabase = true
supabase_host = "db.your-project.supabase.co"
supabase_url = "https://your-project.supabase.co"
supabase_user = "postgres"
supabase_password = "your-database-password"
```

#### Option C: AWS RDS PostgreSQL

```hcl
# In terraform.tfvars
use_supabase = false
db_instance_class = "db.t3.small"
db_allocated_storage = 20
multi_az = true  # For production
```

### Step 3: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy the infrastructure
terraform apply
```

### Step 4: Verify Deployment

```bash
# Check outputs
terraform output

# Test database connection
terraform output database_host
terraform output supabase_dashboard_url  # If using Supabase
```

## 📝 Configuration Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `project_name` | Name of your project | `"amazcope"` |
| `environment` | Environment name | `"production"` |
| `aws_region` | AWS region | `"us-east-1"` |

### Database Variables

#### Supabase Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `use_supabase` | Yes | Enable Supabase | `true` |
| `supabase_access_token` | Conditional | Supabase API token | - |
| `supabase_org_id` | Conditional | Organization ID | - |
| `supabase_region` | No | Supabase region | `"us-east-1"` |
| `supabase_plan` | No | Supabase plan | `"free"` |
| `supabase_host` | Conditional | Existing project host | - |
| `supabase_url` | Conditional | Existing project URL | - |
| `supabase_user` | Conditional | Database username | - |
| `supabase_password` | Conditional | Database password | - |

#### RDS Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `use_supabase` | Yes | Set to `false` for RDS | - |
| `db_instance_class` | No | RDS instance type | `"db.t3.micro"` |
| `db_allocated_storage` | No | Storage in GB | `20` |
| `db_username` | No | Database username | `"postgres"` |
| `db_name` | No | Database name | `"amazcope"` |
| `multi_az` | No | Multi-AZ deployment | `false` |

### Infrastructure Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `enable_alb` | Enable Application Load Balancer | `true` |
| `vpc_cidr` | VPC CIDR block | `"10.0.0.0/16"` |
| `availability_zones` | AZ list | `["us-east-1a", "us-east-1b"]` |
| `api_cpu` | API task CPU units | `512` |
| `api_memory` | API task memory MB | `1024` |
| `worker_cpu` | Worker task CPU units | `256` |
| `worker_memory` | Worker task memory MB | `512` |

## 🔄 Migration Between Database Types

### From RDS to Supabase

1. **Export RDS data:**
```bash
pg_dump postgresql://user:pass@rds-endpoint:5432/dbname > backup.sql
```

2. **Update terraform.tfvars:**
```hcl
use_supabase = true
supabase_access_token = "your-token"
supabase_org_id = "your-org-id"
```

3. **Apply Terraform changes:**
```bash
terraform apply
```

4. **Import data to Supabase:**
```bash
psql postgresql://postgres:password@db.project.supabase.co:5432/postgres < backup.sql
```

### From Supabase to RDS

1. **Export Supabase data:**
```bash
pg_dump postgresql://postgres:pass@db.project.supabase.co:5432/postgres > backup.sql
```

2. **Update terraform.tfvars:**
```hcl
use_supabase = false
db_instance_class = "db.t3.small"
```

3. **Apply Terraform changes:**
```bash
terraform apply
```

4. **Import data to RDS:**
```bash
psql postgresql://postgres:password@rds-endpoint:5432/amazcope < backup.sql
```

## 🛠️ Operations

### Scaling ECS Services

```hcl
# In terraform.tfvars
api_min_capacity = 2
api_max_capacity = 20
worker_min_capacity = 1
worker_max_capacity = 10
```

### Updating Database Configuration

For RDS:
```bash
# Update terraform.tfvars
db_instance_class = "db.t3.medium"  # Upgrade instance

# Apply changes
terraform apply
```

For Supabase:
```bash
# Supabase scaling is automatic
# Update plan if needed:
supabase_plan = "pro"

terraform apply
```

### Backup and Recovery

#### Supabase
- Automatic point-in-time recovery (7 days free, 30 days pro+)
- Manual backups via dashboard or API
- Automatic daily backups

#### RDS
- Automated backups (configurable retention)
- Manual snapshots
- Point-in-time recovery

### Monitoring

Access monitoring dashboards:
- **CloudWatch**: AWS native monitoring
- **Supabase Dashboard**: Database metrics (if using Supabase)
- **ECS Console**: Container metrics
- **Application Logs**: CloudWatch Logs

## 🔒 Security

### Network Security
- Private subnets for database and worker tasks
- Security groups with minimal required access
- NAT Gateway for outbound internet access

### Secrets Management
- AWS Secrets Manager for all sensitive data
- Automatic secret rotation (configurable)
- IAM roles and policies with least privilege

### Database Security
- **RDS**: VPC-only access, encryption at rest, SSL required
- **Supabase**: Built-in Row Level Security (RLS), connection pooling, SSL

## 🚨 Troubleshooting

### Common Issues

#### "Supabase project creation failed"
```bash
# Check your access token and org ID
terraform output supabase_access_token  # Should not be empty
terraform output supabase_org_id       # Should not be empty

# Verify token at: https://app.supabase.com/account/tokens
```

#### "RDS connection timeout"
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids $(terraform output rds_security_group_id)

# Verify subnets
terraform output private_subnet_ids
```

#### "ECS tasks failing to start"
```bash
# Check ECS service events
aws ecs describe-services --cluster $(terraform output ecs_cluster_name) --services api worker

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /ecs/amazcope
```

### Recovery Procedures

#### Database Recovery
```bash
# For RDS - restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier amazcope-restored \
  --db-snapshot-identifier your-snapshot-id

# For Supabase - use dashboard or CLI
supabase db reset --project-ref your-project-id
```

#### Infrastructure Recovery
```bash
# Re-import existing resources
terraform import aws_ecs_cluster.main cluster-name
terraform import aws_rds_instance.postgres db-instance-id

# Recreate from state
terraform apply -auto-approve
```

## 📚 Additional Resources

### Documentation
- [Supabase Documentation](https://supabase.com/docs)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Monitoring Dashboards
- Supabase: `https://app.supabase.com/project/[project-id]`
- AWS Console: `https://console.aws.amazon.com/ecs/`
- CloudWatch: `https://console.aws.amazon.com/cloudwatch/`

### Support
- 🐛 **Issues**: Create GitHub issues for bugs
- 💬 **Discussions**: Use GitHub discussions for questions
- 📧 **Enterprise**: Contact for enterprise support options

---

**Last Updated**: January 2025
**Terraform Version**: 1.5+
**AWS Provider Version**: ~> 5.0
**Supabase Provider Version**: ~> 1.0
