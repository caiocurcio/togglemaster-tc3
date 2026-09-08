# Usado so para pegar o Account ID da conta autenticada no momento do apply.
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "terraform_state" {
  # Nomes de bucket S3 sao unicos GLOBALMENTE (entre todas as contas AWS do mundo).
  # Colar o account_id no nome garante unicidade sem precisar de um recurso "random".
  bucket = "${var.project_name}-tfstate-${data.aws_caller_identity.current.account_id}"

  # Trava de seguranca: um "terraform destroy" rodado por engano no bootstrap
  # nao pode apagar o bucket que guarda o state de todo o resto do projeto.
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
    Purpose   = "remote-state"
  }
}

# Versionamento: se o state for sobrescrito ou corrompido, da pra restaurar uma versao anterior do objeto no S3.
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Criptografia server-side por padrao (AES256), mesmo que o state acabe tendo dado sensivel.
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloqueia qualquer possibilidade do bucket (ou objetos dele) virarem publicos.
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
