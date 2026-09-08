output "state_bucket_name" {
  description = "Nome do bucket S3 a ser usado no backend remoto (infra/envs/*)"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "state_bucket_region" {
  description = "Regiao do bucket de state"
  value       = var.aws_region
}
