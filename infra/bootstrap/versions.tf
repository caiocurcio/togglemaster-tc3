terraform {
  # >= 1.10 porque e a versao que introduziu o lock nativo em S3 (use_lockfile),
  # usado no backend remoto do ambiente dev (sem precisar de tabela DynamoDB pra lock).
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}
