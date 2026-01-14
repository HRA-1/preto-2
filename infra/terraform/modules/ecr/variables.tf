# ========================================
# ECR 모듈 변수
# ========================================

variable "repository_name" {
  description = "ECR 리포지토리 이름"
  type        = string
}

variable "image_tag_mutability" {
  description = "이미지 태그 변경 가능 여부 (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.image_tag_mutability)
    error_message = "image_tag_mutability는 MUTABLE 또는 IMMUTABLE이어야 합니다."
  }
}

variable "scan_on_push" {
  description = "이미지 푸시 시 자동 스캔 여부"
  type        = bool
  default     = true
}

variable "lifecycle_policy_count" {
  description = "보존할 이미지 개수"
  type        = number
  default     = 5

  validation {
    condition     = var.lifecycle_policy_count >= 1
    error_message = "lifecycle_policy_count는 1 이상이어야 합니다."
  }
}

variable "tags" {
  description = "리소스에 적용할 태그"
  type        = map(string)
  default     = {}
}
