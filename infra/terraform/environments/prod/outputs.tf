# ========================================
# 출력값
# ========================================

# ECR
output "ecr_repository_url" {
  description = "ECR 리포지토리 URL"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "ECR 리포지토리 이름"
  value       = module.ecr.repository_name
}

# ECS
output "ecs_cluster_name" {
  description = "ECS 클러스터 이름"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS 서비스 이름"
  value       = module.ecs.service_name
}

output "ecs_task_definition_arn" {
  description = "Task Definition ARN"
  value       = module.ecs.task_definition_arn
}

# Network
output "alb_dns_name" {
  description = "ALB DNS 이름 (애플리케이션 접속 URL)"
  value       = module.network.alb_dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = module.network.alb_arn
}

output "target_group_arn" {
  description = "Target Group ARN"
  value       = module.network.target_group_arn
}

# CloudWatch
output "log_group_name" {
  description = "CloudWatch Log Group 이름"
  value       = module.ecs.log_group_name
}

# IAM
output "task_execution_role_arn" {
  description = "Task Execution Role ARN"
  value       = module.iam.task_execution_role_arn
}

output "task_role_arn" {
  description = "Task Role ARN"
  value       = module.iam.task_role_arn
}
