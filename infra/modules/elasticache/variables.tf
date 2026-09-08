variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  description = "Subnets (privadas) usadas pelo Cache Subnet Group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security groups que podem se conectar na porta 6379 (ex: SG dos nodes do EKS)"
  type        = list(string)
}

variable "node_type" {
  type    = string
  default = "cache.t3.micro"
}

variable "engine_version" {
  type    = string
  default = "7.1"
}
