# Configuracao "parcial": os valores reais (nome do bucket, etc.) vem do
# arquivo backend.hcl (nao versionado - veja backend.hcl.example), via:
#   terraform init -backend-config=backend.hcl
terraform {
  backend "s3" {}
}
