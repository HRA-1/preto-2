# ========================================
# Auto Scaling 모듈 변수
# ========================================

# ECS 서비스 정보 (필수)
variable "cluster_name" {
  description = "ECS 클러스터 이름"
  type        = string
}

variable "service_name" {
  description = "ECS 서비스 이름"
  type        = string
}

# 스케일링 범위
variable "min_capacity" {
  description = "최소 태스크 수"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "최대 태스크 수"
  type        = number
  default     = 4
}

# CPU 스케일링 설정
variable "cpu_target_value" {
  description = "CPU 사용률 목표값 (%)"
  type        = number
  default     = 70
}

variable "cpu_scale_in_cooldown" {
  description = "CPU 스케일 인 쿨다운 (초)"
  type        = number
  default     = 300
}

variable "cpu_scale_out_cooldown" {
  description = "CPU 스케일 아웃 쿨다운 (초)"
  type        = number
  default     = 60
}

# 메모리 스케일링 설정
variable "memory_target_value" {
  description = "메모리 사용률 목표값 (%)"
  type        = number
  default     = 70
}

variable "memory_scale_in_cooldown" {
  description = "메모리 스케일 인 쿨다운 (초)"
  type        = number
  default     = 300
}

variable "memory_scale_out_cooldown" {
  description = "메모리 스케일 아웃 쿨다운 (초)"
  type        = number
  default     = 60
}
