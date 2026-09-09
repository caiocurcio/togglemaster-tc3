output "role_arn" {
  description = "ARN da role que o GitHub Actions assume (usada no workflow com aws-actions/configure-aws-credentials)"
  value       = aws_iam_role.github_actions.arn
}
