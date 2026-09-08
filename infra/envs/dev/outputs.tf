output "cluster_name" {
  value = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "Rode isso pra configurar o kubectl local apontando pro cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "rds_endpoints" {
  value = module.rds.endpoints
}

output "rds_secret_arns" {
  description = "ARNs dos secrets no Secrets Manager com usuario/senha/host de cada banco"
  value       = module.rds.secret_arns
}

output "redis_endpoint" {
  value = module.elasticache.endpoint
}

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}

output "sqs_queue_url" {
  value = module.sqs.queue_url
}

output "evaluation_irsa_role_arn" {
  value = aws_iam_role.evaluation.arn
}

output "analytics_irsa_role_arn" {
  value = aws_iam_role.analytics.arn
}
