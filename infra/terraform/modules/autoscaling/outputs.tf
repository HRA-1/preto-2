# ========================================
# Auto Scaling 모듈 출력값
# ========================================

output "autoscaling_target_id" {
  description = "Auto Scaling Target ID"
  value       = aws_appautoscaling_target.this.id
}

output "cpu_policy_arn" {
  description = "CPU Auto Scaling Policy ARN"
  value       = aws_appautoscaling_policy.cpu.arn
}

output "memory_policy_arn" {
  description = "Memory Auto Scaling Policy ARN"
  value       = aws_appautoscaling_policy.memory.arn
}

output "min_capacity" {
  description = "최소 태스크 수"
  value       = aws_appautoscaling_target.this.min_capacity
}

output "max_capacity" {
  description = "최대 태스크 수"
  value       = aws_appautoscaling_target.this.max_capacity
}
