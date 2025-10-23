variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "amazcope"
}

# Database
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "amazon_monitor"
}

# Redis
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# ECS
variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "ECS task memory in MiB"
  type        = number
  default     = 512
}

variable "backend_desired_count" {
  description = "Desired number of backend task instances"
  type        = number
  default     = 1
}

variable "celery_desired_count" {
  description = "Desired number of celery task instances"
  type        = number
  default     = 1
}

# Networking
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# External services
variable "backendfy_backend_token" {
  description = "backendfy backend token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_backend_key" {
  description = "OpenAI backend key"
  type        = string
  sensitive   = true
  default     = ""
}

# PostgreSQL Database Configuration (External/Direct Credentials)
variable "postgres_host" {
  description = "PostgreSQL database host (e.g., your-db.example.com or Supabase pooler)"
  type        = string
  sensitive   = false
}

variable "postgres_port" {
  description = "PostgreSQL database port"
  type        = string
  default     = "5432"
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "postgres"
}

variable "postgres_user" {
  description = "PostgreSQL database username"
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}


# Application secrets
variable "app_secret_key" {
  description = "Application secret key (will be generated if empty)"
  type        = string
  sensitive   = true
  default     = ""
}

# Sentry Configuration
variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  sensitive   = true
  default     = ""
}

variable "sentry_environment" {
  description = "Sentry environment name"
  type        = string
  default     = "production"
}

variable "sentry_traces_sample_rate" {
  description = "Sentry traces sample rate (0.0 to 1.0)"
  type        = number
  default     = 1.0
}

# Zeabur Configuration
variable "zeabur_project_id" {
  description = "Zeabur project ID"
  type        = string
  default     = ""
}

variable "zeabur_service_name" {
  description = "Zeabur service name"
  type        = string
  default     = "amazcope"
}

variable "zeabur_region" {
  description = "Zeabur deployment region"
  type        = string
  default     = "us-west1"
}

variable "zeabur_app_url" {
  description = "Zeabur application URL (e.g., https://your-app.zeabur.app)"
  type        = string
  default     = ""
}

# Application Configuration
variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cors_origins" {
  description = "Allowed CORS origins (comma-separated)"
  type        = string
  default     = "*"
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "celery_celerys_count" {
  description = "Number of Dragatiq celerys"
  type        = number
  default     = 4
}

variable "rate_limit_per_minute" {
  description = "backend rate limit per minute per user"
  type        = number
  default     = 60
}

# Monitoring
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for CloudWatch alarms"
  type        = string
  default     = ""
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = false
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_alb" {
  description = "Enable Application Load Balancer (set to false for free tier)"
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "Enable S3 + CloudFront hosting for frontend"
  type        = bool
  default     = true
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Tags
variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# Monitoring
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "pagerduty_service_key" {
  description = "PagerDuty service integration key for critical alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for monitoring alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_managed_prometheus" {
  description = "Enable AWS Managed Prometheus for production monitoring"
  type        = bool
  default     = false
}

variable "enable_managed_grafana" {
  description = "Enable AWS Managed Grafana for production monitoring"
  type        = bool
  default     = false
}

# Missing variables for RDS module compatibility
variable "multi_az" {
  description = "Enable Multi-AZ for RDS instance"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Backup retention period in days for RDS"
  type        = number
  default     = 7
}

variable "region" {
  description = "AWS region (alias for aws_region)"
  type        = string
  default     = ""
}

variable "environment_name" {
  description = "Environment name for resource naming (alias for environment)"
  type        = string
  default     = ""
}

variable "project_base_name" {
  description = "Base project name for resource naming (alias for project_name)"
  type        = string
  default     = ""
}

variable "celery_cpu" {
  description = "CPU units for celery task (if different from ecs_task_cpu)"
  type        = number
  default     = null
}

variable "celery_memory" {
  description = "Memory (MB) for celery task (if different from ecs_task_memory)"
  type        = number
  default     = null
}

# Frontend Hosting Variables
variable "frontend_domain" {
  description = "Custom domain name for frontend (optional)"
  type        = string
  default     = ""
}

variable "ssl_certificate_arn" {
  description = "ACM certificate ARN for custom domain (required if frontend_domain is set)"
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100" # Use only US, Canada, Europe for cost optimization

  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200",
      "PriceClass_100"
    ], var.cloudfront_price_class)
    error_message = "CloudFront price class must be PriceClass_All, PriceClass_200, or PriceClass_100."
  }
}

variable "enable_cloudfront_logs" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false # Disabled by default to reduce costs
}
