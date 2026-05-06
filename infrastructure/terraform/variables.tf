# ── General ──────────────────────────────────────────────────────────────────
variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "inframind-ai"
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# ── Lambda ───────────────────────────────────────────────────────────────────
variable "lambda_artifact_s3_key" {
  description = "S3 key for the Lambda deployment package"
  type        = string
  default     = "lambda/inframind-api.zip"
}

variable "lambda_handler" {
  description = "Lambda handler entrypoint (file.function)"
  type        = string
  default     = "index.handler"
}

variable "lambda_runtime" {
  description = "Lambda runtime identifier"
  type        = string
  default     = "nodejs20.x"
}

variable "lambda_memory_mb" {
  description = "Lambda allocated memory in megabytes"
  type        = number
  default     = 256
}

variable "lambda_timeout_sec" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for the API Gateway. Restrict to specific domains in production."
  type        = list(string)
  default     = ["*"]
}

  description = "Environment variables injected into the Lambda function"
  type        = map(string)
  default     = {}
  sensitive   = true
}
