variable "project_name" {
  type = string
}

variable "github_repo" {
  description = "Repositorio no formato \"owner/repo\" que tera permissao de assumir a role via OIDC"
  type        = string
}

variable "ecr_repository_arns" {
  description = "ARNs dos repositorios ECR que o pipeline de CI tem permissao de fazer push"
  type        = list(string)
}
