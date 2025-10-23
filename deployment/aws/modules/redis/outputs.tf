output "redis_replication_group_id" {
  description = "ID of the Redis replication group"
  value       = aws_elasticache_replication_group.main.id
}

output "redis_primary_endpoint" {
  description = "Primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint address"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = 6379
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

output "redis_auth_token_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the auth token"
  value       = var.enable_transit_encryption ? aws_secretsmanager_secret.redis_auth_token[0].arn : null
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = var.enable_transit_encryption ? "rediss://:AUTH_TOKEN@${aws_elasticache_replication_group.main.primary_endpoint_address}:6379" : "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379"
  sensitive   = true
}
