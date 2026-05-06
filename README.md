# inframind-ai

AI-powered infrastructure management platform.

---

## Repository structure

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint, test, Terraform validate on every PR/push
│       ├── terraform.yml        # Terraform plan (PRs) / apply (merges)
│       ├── deploy-lambda.yml    # Build, upload & deploy AWS Lambda
│       └── deploy-vercel.yml    # Build & deploy Next.js frontend to Vercel
├── infrastructure/
│   └── terraform/
│       ├── main.tf              # Root module – wires all sub-modules together
│       ├── variables.tf
│       ├── outputs.tf
│       ├── modules/
│       │   ├── api_gateway/     # HTTP API Gateway v2 + CloudWatch logs
│       │   ├── iam/             # Lambda execution role & policies
│       │   ├── lambda/          # Lambda function + CloudWatch alarm
│       │   └── s3/              # Artifacts & logs buckets
│       └── envs/
│           ├── dev/             # terraform.tfvars + backend.tfvars
│           ├── staging/
│           └── prod/
├── lambda/
│   ├── src/index.js             # Lambda handler entry point
│   └── package.json
├── scripts/
│   └── package-lambda.sh        # Packages lambda/ into lambda.zip
├── vercel.json                  # Vercel project configuration
└── .env.example                 # Environment variable template
```

---

## Infrastructure (Terraform)

### Prerequisites

- [Terraform ≥ 1.5](https://developer.hashicorp.com/terraform/downloads)
- AWS credentials with sufficient permissions
- An S3 bucket + DynamoDB table for remote state (names configured in `envs/<env>/backend.tfvars`)

### Bootstrap remote state (one-time)

```bash
aws s3 mb s3://inframind-ai-tfstate --region us-east-1
aws dynamodb create-table \
  --table-name inframind-ai-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Deploy an environment

```bash
cd infrastructure/terraform

# Initialise with environment-specific backend
terraform init -backend-config="envs/dev/backend.tfvars"

# Review the plan
terraform plan -var-file="envs/dev/terraform.tfvars"

# Apply
terraform apply -var-file="envs/dev/terraform.tfvars"
```

Replace `dev` with `staging` or `prod` as needed.

---

## Lambda deployment

### Local packaging

```bash
# Install production deps first
(cd lambda && npm ci --omit=dev)

# Create lambda.zip
bash scripts/package-lambda.sh
```

### Manual deploy

```bash
# Upload to S3
aws s3 cp lambda.zip s3://inframind-ai-dev-artifacts/lambda/inframind-api.zip

# Update function code
aws lambda update-function-code \
  --function-name inframind-ai-dev-api \
  --s3-bucket inframind-ai-dev-artifacts \
  --s3-key lambda/inframind-api.zip \
  --publish
```

---

## Frontend (Vercel)

The project is configured as a Next.js app deployed via Vercel.

| Branch    | Vercel target  |
|-----------|---------------|
| `main`    | Production     |
| any other | Preview        |

### Required Vercel secrets (GitHub Actions)

| Secret              | Description               |
|---------------------|---------------------------|
| `VERCEL_TOKEN`      | Vercel personal API token |
| `VERCEL_ORG_ID`     | Vercel org/team ID        |
| `VERCEL_PROJECT_ID` | Vercel project ID         |

---

## CI/CD workflows

| Workflow              | Trigger                          | Actions                                     |
|-----------------------|----------------------------------|---------------------------------------------|
| `ci.yml`              | Push / PR to any branch          | Lint · Test · Terraform fmt + validate      |
| `terraform.yml`       | Push / PR touching `infra/**`    | Plan (PR) · Apply (merge to main/develop)   |
| `deploy-lambda.yml`   | Push to `main`/`develop`         | Build → S3 upload → Terraform apply → smoke |
| `deploy-vercel.yml`   | Push / PR touching `frontend/**` | Vercel build + deploy                       |

### Required AWS secrets (GitHub Actions)

| Secret                  | Description               |
|-------------------------|---------------------------|
| `AWS_ACCESS_KEY_ID`     | IAM key with deploy perms |
| `AWS_SECRET_ACCESS_KEY` | IAM secret                |

---

## Environment variables

Copy `.env.example` to `.env.local` and fill in the values:

```bash
cp .env.example .env.local
```

See `infrastructure/terraform/envs/<env>/.env` for per-environment defaults.
