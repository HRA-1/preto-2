# ========================================
# ECS 모듈 변수
# ========================================

# 기본 정보
variable "cluster_name" {
  description = "ECS 클러스터 이름"
  type        = string
}

variable "service_name" {
  description = "ECS 서비스 이름"
  type        = string
}

variable "task_family" {
  description = "Task Definition 패밀리 이름"
  type        = string
}

variable "container_name" {
  description = "컨테이너 이름"
  type        = string
}

# 컨테이너 설정
variable "container_image" {
  description = "Docker 이미지 URL"
  type        = string
}

variable "container_port" {
  description = "컨테이너 포트"
  type        = number
  default     = 8501
}

variable "environment_variables" {
  description = "컨테이너 환경 변수"
  type        = map(string)
  default     = {}
}

# 리소스 할당
variable "cpu" {
  description = "Task CPU (Fargate 유효 값: 256, 512, 1024, 2048, 4096)"
  type        = string
  default     = "2048"

  validation {
    condition     = contains(["256", "512", "1024", "2048", "4096"], var.cpu)
    error_message = "CPU는 유효한 Fargate 값이어야 합니다."
  }
}

variable "memory" {
  description = "Task 메모리 (MB)"
  type        = string
  default     = "4096"
}

variable "cpu_architecture" {
  description = "CPU 아키텍처 (X86_64 or ARM64)"
  type        = string
  default     = "ARM64"

  validation {
    condition     = contains(["X86_64", "ARM64"], var.cpu_architecture)
    error_message = "cpu_architecture는 X86_64 또는 ARM64이어야 합니다."
  }
}

# 서비스 설정
variable "desired_count" {
  description = "실행할 Task 수"
  type        = number
  default     = 1
}

variable "health_check_grace_period" {
  description = "헬스 체크 유예 기간 (초)"
  type        = number
  default     = 300
}

# IAM
variable "task_execution_role_arn" {
  description = "Task Execution Role ARN"
  type        = string
}

variable "task_role_arn" {
  description = "Task Role ARN"
  type        = string
}

# 네트워킹
variable "subnets" {
  description = "서브넷 ID 목록"
  type        = list(string)
}

variable "security_groups" {
  description = "보안 그룹 ID 목록"
  type        = list(string)
}

variable "assign_public_ip" {
  description = "퍼블릭 IP 할당 여부"
  type        = bool
  default     = true
}

# 로드 밸런서
variable "target_group_arn" {
  description = "ALB Target Group ARN"
  type        = string
}

# CloudWatch Logs
variable "log_group_name" {
  description = "CloudWatch Log Group 이름"
  type        = string
}

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

# 태그
variable "tags" {
  description = "리소스에 적용할 태그"
  type        = map(string)
  default     = {}
}
