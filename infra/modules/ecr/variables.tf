variable "project_name" {
  type = string
}

variable "service_names" {
  description = "Um repositorio ECR por microsservico"
  type        = list(string)
  default     = ["auth", "flag", "targeting", "evaluation", "analytics"]
}

variable "image_tag_mutability" {
  description = "IMMUTABLE impede sobrescrever uma tag ja publicada (ex: reenviar 'v1.0.0-a1b2c3d' com outro conteudo)"
  type        = string
  default     = "IMMUTABLE"
}

variable "scan_on_push" {
  description = "Scan de vulnerabilidades nativo do ECR a cada push (alem do Trivy rodado no pipeline de CI)"
  type        = bool
  default     = true
}
