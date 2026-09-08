output "security_group_id" {
  value = aws_security_group.rds.id
}

output "endpoints" {
  description = "Endereco (host) de cada banco, por chave de servico"
  value       = { for k, v in aws_db_instance.this : k => v.address }
}

output "secret_arns" {
  description = "ARN do Secrets Manager com as credenciais de cada banco, por chave de servico"
  value       = { for k, v in aws_secretsmanager_secret.db : k => v.arn }
}
