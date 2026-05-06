environment        = "staging"
aws_region         = "us-east-1"
lambda_memory_mb   = 512
lambda_timeout_sec = 30
lambda_runtime     = "nodejs20.x"
lambda_handler     = "index.handler"
cors_allow_origins = ["https://staging.inframind.ai"]
