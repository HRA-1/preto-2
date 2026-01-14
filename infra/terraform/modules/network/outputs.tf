# ========================================
# Network 모듈 출력값
# ========================================

output "vpc_id" {
  description = "VPC ID"
  value       = data.aws_vpc.this.id
}

output "subnet_ids" {
  description = "서브넷 ID 목록"
  value       = data.aws_subnets.this.ids
}

output "security_group_id" {
  description = "보안 그룹 ID"
  value       = data.aws_security_group.this.id
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.this.arn
}

output "alb_dns_name" {
  description = "ALB DNS 이름"
  value       = aws_lb.this.dns_name
}

output "alb_zone_id" {
  description = "ALB Zone ID"
  value       = aws_lb.this.zone_id
}

output "target_group_arn" {
  description = "Target Group ARN"
  value       = aws_lb_target_group.this.arn
}

output "target_group_name" {
  description = "Target Group 이름"
  value       = aws_lb_target_group.this.name
}

output "listener_arn" {
  description = "HTTP Listener ARN"
  value       = aws_lb_listener.http.arn
}
