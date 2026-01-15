# ========================================
# 프로젝트 기본 정보
# ========================================
variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "preto-2"
}

variable "app_name" {
  description = "애플리케이션 이름"
  type        = string
  default     = "streamlit-app"
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# ========================================
# ECR 설정
# ========================================
variable "image_tag_mutability" {
  description = "이미지 태그 변경 가능 여부"
  type        = string
  default     = "MUTABLE"
}

variable "ecr_lifecycle_count" {
  description = "보존할 이미지 개수"
  type        = number
  default     = 2
}

# ========================================
# ECS 설정
# ========================================
variable "ecs_cpu" {
  description = "ECS 태스크 CPU"
  type        = string
  default     = "512"
}

variable "ecs_memory" {
  description = "ECS 태스크 메모리 (MB)"
  type        = string
  default     = "1024"
}

variable "ecs_desired_count" {
  description = "실행할 태스크 수"
  type        = number
  default     = 1
}

variable "container_port" {
  description = "컨테이너 포트"
  type        = number
  default     = 8501
}

variable "cpu_architecture" {
  description = "CPU 아키텍처"
  type        = string
  default     = "ARM64"
}

# ========================================
# 기존 인프라 참조
# ========================================
# preto-1과 동일한 VPC/Subnet/Security Group 사용
variable "vpc_id" {
  description = "기존 VPC ID"
  type        = string
  default     = "vpc-0c11696cf8468ca8e"
}

variable "subnet_ids" {
  description = "기존 서브넷 ID 목록"
  type        = list(string)
  default = [
    "subnet-0cd2fcdff481b49c2",
    "subnet-0892735c449ac40db"
  ]
}

variable "security_group_id" {
  description = "기존 보안 그룹 ID"
  type        = string
  default     = "sg-0193a7c1c72f2a43c"
}

# ========================================
# Auto Scaling 설정
# ========================================
variable "autoscaling_enabled" {
  description = "Auto Scaling 활성화 여부"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "최소 태스크 수"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "최대 태스크 수"
  type        = number
  default     = 4
}

variable "autoscaling_cpu_target" {
  description = "CPU 사용률 목표값 (%)"
  type        = number
  default     = 70
}

variable "autoscaling_memory_target" {
  description = "메모리 사용률 목표값 (%)"
  type        = number
  default     = 70
}
