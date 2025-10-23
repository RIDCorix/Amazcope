# Main Terraform Configuration
# Amazcope - Production Infrastructure with Supabase

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket  = "amazcope-terraform-state"
    key     = "amazon-monitor/terraform.tfstate"
    region  = "ap-southeast-1"
    encrypt = true
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Local Variables
locals {
  project_name      = var.project_name
  environment       = var.environment
  project_full_name = "${local.project_name}-${local.environment}"

  # Alias variables for compatibility
  region            = var.region != "" ? var.region : var.aws_region
  environment_name  = var.environment_name != "" ? var.environment_name : var.environment
  project_base_name = var.project_base_name != "" ? var.project_base_name : var.project_name

  common_tags = merge(
    var.additional_tags,
    {
      Project     = local.project_name
      Environment = local.environment
      ManagedBy   = "Terraform"
      Repository  = "amazcope"
    }
  )
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name         = local.project_name
  vpc_cidr             = var.vpc_cidr
  availability_zones   = slice(data.aws_availability_zones.available.names, 0, var.az_count)
  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpc_flow_logs = var.enable_vpc_flow_logs
  common_tags          = local.common_tags
}

# RDS Module - Disabled (using external PostgreSQL)
# module "rds" {
#   source = "./modules/rds"

#   project_name       = local.project_name
#   vpc_id             = module.vpc.vpc_id
#   vpc_cidr           = var.vpc_cidr
#   private_subnet_ids = module.vpc.private_subnet_ids

#   instance_class        = var.db_instance_class
#   allocated_storage     = var.db_allocated_storage
#   database_name         = var.db_name
#   master_username       = var.db_username
#   multi_az              = var.multi_az
#   backup_retention_days = var.backup_retention_period
#   deletion_protection   = false # Set to false for development

#   common_tags = local.common_tags
# }

# Redis Module
module "redis" {
  source = "./modules/redis"

  project_name            = local.project_name
  vpc_id                  = module.vpc.vpc_id
  vpc_cidr                = module.vpc.vpc_cidr
  private_subnet_ids      = module.vpc.private_subnet_ids
  allowed_security_groups = []

  skip_final_snapshot = var.environment != "production"

  enable_cloudwatch_alarms = var.enable_monitoring
  alarm_sns_topic_arn      = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : null
  notification_topic_arn   = var.enable_monitoring ? aws_sns_topic.alerts[0].arn : null

  common_tags = local.common_tags
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  count = var.enable_monitoring ? 1 : 0
  name  = "${local.project_name}-alerts"
  tags  = local.common_tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.enable_monitoring && var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Secrets Manager for Application Secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.project_name}-app-secrets"
  recovery_window_in_days = 7
  description             = "Application secrets for ${local.project_name}"
  tags                    = local.common_tags
}

# Random passwords for app secrets if not provided
resource "random_password" "app_secret" {
  length  = 64
  special = true
}

resource "random_password" "secret_key" {
  length  = 64
  special = true
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Secrets Manager Secret Version - Direct PostgreSQL Configuration
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    # Database connection details (direct credentials)
    POSTGRES_HOST     = var.postgres_host
    POSTGRES_PORT     = var.postgres_port
    POSTGRES_DB       = var.postgres_db
    POSTGRES_USER     = var.postgres_user
    POSTGRES_PASSWORD = var.postgres_password
    DATABASE_URL      = "postgresql://${var.postgres_user}:${var.postgres_password}@${var.postgres_host}:${var.postgres_port}/${var.postgres_db}"

    # Redis connection
    REDIS_URL  = module.redis.redis_connection_string
    REDIS_HOST = module.redis.redis_primary_endpoint
    REDIS_PORT = "6379"

    # Application secrets
    SECRET_KEY      = var.jwt_secret_key != "" ? var.jwt_secret_key : random_password.secret_key.result
    JWT_SECRET_KEY  = random_password.jwt_secret.result
    APIFY_API_TOKEN = var.backendfy_backend_token
    OPENAI_API_KEY  = var.openai_backend_key
    SENTRY_DSN      = var.sentry_dsn
    ENVIRONMENT     = var.environment
  })
}
