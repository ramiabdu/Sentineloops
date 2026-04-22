output "service_role_arn" {
  description = "ARN of the SentinelOps service role."
  value       = aws_iam_role.service.arn
}
