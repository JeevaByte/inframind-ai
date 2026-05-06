output "api_gateway_url" {
  description = "Base URL of the deployed API Gateway stage"
  value       = module.api_gateway.invoke_url
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = module.lambda.function_arn
}

output "artifacts_bucket_name" {
  description = "S3 bucket used for Lambda deployment artifacts"
  value       = module.s3.artifacts_bucket_id
}

output "lambda_role_arn" {
  description = "IAM role ARN assumed by the Lambda function"
  value       = module.iam.lambda_role_arn
}
