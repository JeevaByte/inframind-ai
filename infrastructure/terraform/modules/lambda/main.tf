variable "environment"        { type = string }
variable "project"            { type = string }
variable "lambda_role_arn"    { type = string }
variable "artifact_s3_bucket" { type = string }
variable "artifact_s3_key"    { type = string }
variable "lambda_handler"     { type = string }
variable "lambda_runtime"     { type = string }
variable "lambda_memory_mb"   { type = number }
variable "lambda_timeout_sec" { type = number }
variable "environment_vars"   {
  type      = map(string)
  default   = {}
  sensitive = true
}

locals {
  function_name = "${var.project}-${var.environment}-api"
}

# ── Lambda function ───────────────────────────────────────────────────────────
resource "aws_lambda_function" "api" {
  function_name = local.function_name
  description   = "InfraMind AI API – ${var.environment}"

  s3_bucket = var.artifact_s3_bucket
  s3_key    = var.artifact_s3_key

  handler     = var.lambda_handler
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_mb
  timeout     = var.lambda_timeout_sec
  role        = var.lambda_role_arn

  dynamic "environment" {
    for_each = length(var.environment_vars) > 0 ? [1] : []
    content {
      variables = var.environment_vars
    }
  }

  tracing_config { mode = "Active" }

  lifecycle {
    ignore_changes = [s3_key] # updated by CI/CD
  }
}

# ── CloudWatch log group ──────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30
}

# ── CloudWatch alarm: errors ─────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda error rate too high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

output "function_name" { value = aws_lambda_function.api.function_name }
output "function_arn"  { value = aws_lambda_function.api.arn }
output "invoke_arn"    { value = aws_lambda_function.api.invoke_arn }
