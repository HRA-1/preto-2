# ========================================
# IAM 모듈 변수
# ========================================

variable "name_prefix" {
  description = "IAM 역할 이름 접두사"
  type        = string
}

variable "tags" {
  description = "리소스에 적용할 태그"
  type        = map(string)
  default     = {}
}
