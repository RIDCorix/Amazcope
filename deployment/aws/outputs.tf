# Network Infrastructure
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# Database Configuration
output "database_type" {
  description = "Type of database being used"
  value       = "external-postgresql"
}

output "database_host" {
  description = "Database host endpoint"
  value       = var.postgres_host
  sensitive   = false
}

output "database_name" {
  description = "Database name"
  value       = var.postgres_db
}

# Redis
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_primary_endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = 6379
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "alb_dns_name" {
  description = "ALB DNS name (null if ALB disabled)"
  value       = var.enable_alb ? aws_lb.backend[0].dns_name : null
}

output "alb_zone_id" {
  description = "ALB zone ID (null if ALB disabled)"
  value       = var.enable_alb ? aws_lb.backend[0].zone_id : null
}

output "alb_enabled" {
  description = "Whether ALB is enabled"
  value       = var.enable_alb
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.backend.name
}

output "secret_manager_arn" {
  description = "Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.app_secrets.arn
  sensitive   = true
}

# ========================================
# GitHub Secrets Auto-Backfill Outputs
# ========================================
# These outputs are automatically backfilled to GitHub Secrets
# by the CD workflow after terraform apply

output "deploy_host" {
  description = "Deployment server hostname (ALB DNS name or ECS public IP info)"
  value       = var.enable_alb ? aws_lb.backend[0].dns_name : "Direct ECS access - check service in AWS Console"
  sensitive   = false
}

output "app_url" {
  description = "Public application URL"
  value       = var.enable_alb ? "https://${aws_lb.backend[0].dns_name}" : "Direct ECS access on port 8000 - check AWS Console for task public IPs"
  sensitive   = false
}

output "access_method" {
  description = "How to access the application"
  value       = var.enable_alb ? "ALB" : "Direct ECS (public IP on port 8000)"
  sensitive   = false
}

output "zeabur_app_url" {
  description = "Zeabur application URL (if using Zeabur deployment)"
  value       = var.zeabur_app_url
  sensitive   = false
}

output "tg_arn" {
  description = "Target Group ARN (null if ALB disabled)"
  value       = var.enable_alb ? aws_lb_target_group.backend[0].arn : null
}

# Sentry configuration outputs (if using Sentry via Terraform)
# Uncomment these if you manage Sentry via Terraform provider
# output "sentry_org" {
#   description = "Sentry organization slug"
#   value       = sentry_organization.main.slug
#   sensitive   = false
# }

# output "sentry_project" {
#   description = "Sentry project name"
#   value       = sentry_project.main.name
#   sensitive   = false
# }

# output "sentry_auth_token" {
#   description = "Sentry authentication token"
#   value       = sentry_key.main.dsn_secret
#   sensitive   = true
# }

# Frontend Hosting Infrastructure
output "s3_bucket_name" {
  description = "S3 bucket name for frontend hosting"
  value       = aws_s3_bucket.frontend.bucket
}

output "s3_bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.frontend.bucket_domain_name
}
