output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  value = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_security_group_id" {
  value = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "oidc_provider_arn" {
  description = "ARN do OIDC provider do cluster, usado para criar roles IRSA"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  description = "URL do OIDC provider sem o prefixo https://, no formato exigido pela trust policy de roles IRSA"
  value       = replace(aws_iam_openid_connect_provider.eks.url, "https://", "")
}

output "node_role_arn" {
  value = aws_iam_role.node.arn
}
