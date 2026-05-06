environment        = "prod"
aws_region         = "us-east-1"
lambda_memory_mb   = 1024
lambda_timeout_sec = 30
lambda_runtime     = "nodejs20.x"
lambda_handler     = "index.handler"
cors_allow_origins = ["https://inframind.ai", "https://www.inframind.ai"]
