output "bucket_name" {
  description = "Private storage bucket name."
  value       = aws_s3_bucket.this.bucket
}
