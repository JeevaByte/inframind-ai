terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    # Configured per environment via -backend-config flags or envs/<env>/backend.tfvars
    key     = "inframind-ai/terraform.tfstate"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "inframind-ai"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ── IAM ──────────────────────────────────────────────────────────────────────
module "iam" {
  source      = "./modules/iam"
  environment = var.environment
  project     = var.project
}

# ── S3 ───────────────────────────────────────────────────────────────────────
module "s3" {
  source      = "./modules/s3"
  environment = var.environment
  project     = var.project
}

# ── Lambda ───────────────────────────────────────────────────────────────────
module "lambda" {
  source = "./modules/lambda"

  environment        = var.environment
  project            = var.project
  lambda_role_arn    = module.iam.lambda_role_arn
  artifact_s3_bucket = module.s3.artifacts_bucket_id
  artifact_s3_key    = var.lambda_artifact_s3_key
  lambda_handler     = var.lambda_handler
  lambda_runtime     = var.lambda_runtime
  lambda_memory_mb   = var.lambda_memory_mb
  lambda_timeout_sec = var.lambda_timeout_sec
  environment_vars   = var.lambda_environment_vars
}

# ── API Gateway ───────────────────────────────────────────────────────────────
module "api_gateway" {
  source = "./modules/api_gateway"

  environment          = var.environment
  project              = var.project
  lambda_invoke_arn    = module.lambda.invoke_arn
  lambda_function_name = module.lambda.function_name
  cors_allow_origins   = var.cors_allow_origins
}
