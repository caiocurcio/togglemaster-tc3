variable "project_name" {
  type    = string
  default = "togglemaster"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "azs" {
  description = "Availability Zones usadas (o EKS exige pelo menos 2)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "k8s_namespace" {
  description = "Namespace do Kubernetes onde os microsservicos vao rodar (usado nas roles IRSA)"
  type        = string
  default     = "togglemaster"
}

variable "github_repo" {
  description = "Repositorio GitHub (owner/repo) autorizado a assumir a role de CI via OIDC"
  type        = string
  default     = "caiocurcio/togglemaster-tc3"
}
