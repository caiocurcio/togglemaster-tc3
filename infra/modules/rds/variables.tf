variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  description = "Subnets (privadas) usadas pelo DB Subnet Group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security groups que podem se conectar na porta 5432 (ex: SG dos nodes do EKS)"
  type        = list(string)
}

variable "instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Armazenamento em GB (20GB e o limite do free tier)"
  type        = number
  default     = 20
}

variable "engine_version" {
  type    = string
  default = "15.7"
}

variable "multi_az" {
  description = "Multi-AZ = alta disponibilidade, mas dobra o custo. false para um ambiente de estudo."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  type    = bool
  default = true
}

variable "databases" {
  description = "Um banco por chave. A chave (ex: \"auth\") vira parte do identifier e do nome do secret."
  type = map(object({
    db_name  = string
    username = string
  }))
}
