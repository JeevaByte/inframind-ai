provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "public_app" {
  name = "public-app-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_policy" "admin_like" {
  name   = "hackathon-admin-like"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

resource "aws_db_instance" "customer_db" {
  allocated_storage = 100
  engine            = "postgres"
  instance_class    = "db.m5.4xlarge"
  username          = "admin"
  password          = "supersecretpassword123"
  encrypted         = false
  tags              = {}
}