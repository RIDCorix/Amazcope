# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-cluster"
    }
  )
}

locals {
  # Database configuration - direct PostgreSQL credentials
  db_host = var.postgres_host
  db_port = var.postgres_port
  db_name = var.postgres_db

  # Environment variables for ECS containers
  common_environment = {
    ENVIRONMENT   = var.environment
    POSTGRES_HOST = local.db_host
    POSTGRES_PORT = local.db_port
    POSTGRES_DB   = local.db_name
    REDIS_HOST    = module.redis.redis_primary_endpoint
    REDIS_PORT    = "6379"
  }
  # Combined environment variables
  environment_vars = local.common_environment

  secrets_in_definition = jsonencode([
    for k, v in local.environment_vars : {
      name      = k
      valueFrom = "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${var.environment_name}/${var.project_base_name}/${k}"
    }
  ])
  task_definition_vars = {
    ADDITIONAL_SECRETS = local.secrets_in_definition,
    AWS_ACCOUNT_ID     = data.aws_caller_identity.current.account_id,
    AWS_REGION         = var.region,
    PROJECT_FULL_NAME  = local.project_full_name,
    ENVIRONMENT_NAME   = var.environment_name,
    PROJECT_BASE_NAME  = var.project_base_name
    PROJECT_SECRET_KEY = random_password.project_secret_key.result,
  }

}

resource "random_password" "project_secret_key" {
  length           = 16
  special          = true
  override_special = "_%@"
}

# ECR Repository
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

# CloudWatch Log Group for Backend
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.project_full_name}-backend"
  retention_in_days = 30

  tags = var.tags
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Logs permissions for ECS task execution role
resource "aws_iam_role_policy" "ecs_task_execution_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}*",
          "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}*:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeRepositories",
          "ecr:GetRepositoryPolicy",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PullImage"
        ],
        Resource = "*"
      },
      // S3
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
        ]
        Resource = "arn:aws:s3:::${local.project_full_name}-*"
      },
    ]
  })
}

# ECS Task Role (for application)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Build list of secrets that ECS tasks need access to
locals {
  secrets_to_access = compact([
    aws_secretsmanager_secret.app_secrets.arn,
    # Add Redis auth token secret if Redis auth is enabled
    try(module.redis.redis_auth_token_secret_arn, null)
  ])
}

# Policy for accessing Secrets Manager (for task execution role)
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = local.secrets_to_access
      }
    ]
  })
}

# Policy for accessing Secrets Manager (for task role - if needed at runtime)
resource "aws_iam_role_policy" "ecs_task_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = local.secrets_to_access
      }
    ]
  })
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = module.vpc.vpc_id

  # Allow traffic from ALB when enabled
  dynamic "ingress" {
    for_each = var.enable_alb ? [1] : []
    content {
      from_port       = 8000
      to_port         = 8000
      protocol        = "tcp"
      security_groups = [aws_security_group.alb[0].id]
      description     = "Allow traffic from ALB"
    }
  }

  # Allow direct public access when ALB is disabled (for free tier)
  dynamic "ingress" {
    for_each = var.enable_alb ? [] : [1]
    content {
      from_port   = 8000
      to_port     = 8000
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "Allow direct public access (no ALB)"
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
    }
  )
}

# ECS Task Definition
resource "aws_ecs_task_definition" "backend_td" {
  family                   = "${local.project_full_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "4096"
  memory                   = "30720"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = templatefile("${path.module}/templates/td-backend.json", local.task_definition_vars)
}

# ECS Service
resource "aws_ecs_service" "backend_service" {
  name                   = "${local.project_full_name}-backend"
  cluster                = aws_ecs_cluster.main.id
  task_definition        = aws_ecs_task_definition.backend_td.arn
  desired_count          = 1
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = module.vpc.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  dynamic "load_balancer" {
    for_each = var.enable_alb ? [1] : []
    content {
      target_group_arn = module.alb.tg_arn
      container_name   = "backend"
      container_port   = 8000
    }
  }

}

resource "aws_cloudwatch_log_group" "scheduler" {
  name              = "/ecs/${local.project_full_name}-scheduler"
  retention_in_days = 30

  tags = var.tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "scheduler_td" {
  family                   = "${local.project_full_name}-scheduler"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "4096"
  memory                   = "30720"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = templatefile("${path.module}/templates/td-scheduler.json", local.task_definition_vars)
}

# ECS Service
resource "aws_ecs_service" "scheduler_service" {
  name                   = "${local.project_full_name}-scheduler"
  cluster                = aws_ecs_cluster.main.id
  task_definition        = aws_ecs_task_definition.scheduler_td.arn
  desired_count          = 1
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = module.vpc.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

}
