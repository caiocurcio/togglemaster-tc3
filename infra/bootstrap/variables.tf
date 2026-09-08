variable "aws_region" {
  description = "Regiao AWS onde o bucket de state sera criado"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome do projeto, usado para nomear os recursos"
  type        = string
  default     = "togglemaster"
}
