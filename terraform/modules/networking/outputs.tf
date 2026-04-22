output "vpc_id" {
  description = "Created VPC ID."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Created public subnet IDs."
  value       = values(aws_subnet.public)[*].id
}
