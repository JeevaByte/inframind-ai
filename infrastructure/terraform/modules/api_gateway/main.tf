variable "environment"          { type = string }
variable "project"              { type = string }
variable "lambda_invoke_arn"    { type = string }
variable "lambda_function_name" { type = string }
variable "cors_allow_origins"   {
  description = "List of allowed CORS origins. Override per environment."
  type        = list(string)
  default     = ["*"]
}

locals {
  api_name = "${var.project}-${var.environment}-api-gw"
}

# ── HTTP API (v2) ─────────────────────────────────────────────────────────────
resource "aws_apigatewayv2_api" "api" {
  name          = local.api_name
  protocol_type = "HTTP"
  description   = "InfraMind AI API Gateway – ${var.environment}"

  cors_configuration {
    allow_headers = ["Content-Type", "Authorization"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_origins = var.cors_allow_origins
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn
  }

  default_route_settings {
    throttling_burst_limit   = 500
    throttling_rate_limit    = 1000
    detailed_metrics_enabled = true
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Allow API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# ── CloudWatch log group ──────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/apigateway/${local.api_name}"
  retention_in_days = 30
}

output "api_id"     { value = aws_apigatewayv2_api.api.id }
output "invoke_url" { value = aws_apigatewayv2_stage.default.invoke_url }
