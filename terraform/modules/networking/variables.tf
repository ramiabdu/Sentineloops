variable "name" {
  description = "Name prefix for networking resources."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the SentinelOps VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets."
  type        = list(string)
  default     = ["10.40.1.0/24", "10.40.2.0/24"]
}
