# ========================================
# IAM 모듈 출력값
# ========================================

output "task_execution_role_arn" {
  description = "ECS Task Execution Role ARN"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "task_execution_role_name" {
  description = "ECS Task Execution Role Name"
  value       = aws_iam_role.ecs_task_execution.name
}

output "task_role_arn" {
  description = "ECS Task Role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "task_role_name" {
  description = "ECS Task Role Name"
  value       = aws_iam_role.ecs_task.name
}
