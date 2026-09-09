variable "project_name" {
  description = "Nome do projeto, usado para nomear os recursos"
  type        = string
}

variable "kubernetes_version" {
  description = "Versao do Kubernetes do cluster EKS. Deixe null (padrao) para o Terraform aceitar a versao que a AWS ja provisionou/recomenda, em vez de travar um numero que pode ficar indisponivel com o tempo (foi exatamente isso que aconteceu: pedimos 1.30 e a AWS ja tinha provisionado 1.31)."
  type        = string
  default     = null
}

variable "cluster_subnet_ids" {
  description = "Subnets onde os ENIs do control plane do EKS ficam (recomendado: publicas + privadas, para permitir acesso via endpoint publico)"
  type        = list(string)
}

variable "node_subnet_ids" {
  description = "Subnets onde os nodes (EC2) do Node Group ficam (recomendado: apenas privadas)"
  type        = list(string)
}

variable "node_instance_types" {
  description = "Tipos de instancia EC2 usados pelo Node Group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_ami_type" {
  description = "Tipo de AMI dos nodes. AL2023 e a familia atual recomendada pela AWS (a antiga AL2 vem sendo descontinuada release a release)."
  type        = string
  default     = "AL2023_x86_64_STANDARD"
}

variable "node_capacity_type" {
  description = "ON_DEMAND ou SPOT (SPOT e mais barato, mas os nodes podem ser reclamados pela AWS a qualquer momento)"
  type        = string
  default     = "ON_DEMAND"
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}
