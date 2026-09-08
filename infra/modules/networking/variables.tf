variable "project_name" {
  description = "Nome do projeto, usado para nomear os recursos"
  type        = string
}

variable "vpc_cidr" {
  description = "Bloco CIDR da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability Zones a usar (o EKS exige pelo menos 2)"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Um CIDR de subnet publica por AZ (mesma ordem de var.azs)"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Um CIDR de subnet privada por AZ (mesma ordem de var.azs)"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Cria 1 NAT Gateway (cobrado por hora + trafego) para as subnets privadas terem saida a internet"
  type        = bool
  default     = true
}

variable "public_subnet_extra_tags" {
  description = "Tags extras para as subnets publicas (ex: tag de cluster do EKS, definida no ambiente que usa este modulo)"
  type        = map(string)
  default     = {}
}

variable "private_subnet_extra_tags" {
  description = "Tags extras para as subnets privadas (ex: tag de cluster do EKS)"
  type        = map(string)
  default     = {}
}
