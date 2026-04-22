resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.name}-vpc"
  }
}

resource "aws_subnet" "public" {
  for_each = toset(var.public_subnet_cidrs)

  vpc_id     = aws_vpc.this.id
  cidr_block = each.value

  tags = {
    Name = "${var.name}-public-${replace(each.value, "/", "-")}"
  }
}
