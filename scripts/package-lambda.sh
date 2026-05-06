#!/usr/bin/env bash
# scripts/package-lambda.sh
# Creates lambda.zip containing the Lambda function source + node_modules.
# Run from the repository root after `npm ci --omit=dev` in the lambda/ directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LAMBDA_DIR="${ROOT_DIR}/lambda"
OUTPUT="${ROOT_DIR}/lambda.zip"

echo "==> Packaging Lambda from ${LAMBDA_DIR}"

if [ ! -d "${LAMBDA_DIR}/node_modules" ]; then
  echo "==> Installing production dependencies..."
  (cd "${LAMBDA_DIR}" && npm ci --omit=dev)
fi

rm -f "${OUTPUT}"

cd "${LAMBDA_DIR}"
zip -r "${OUTPUT}" src/ node_modules/ package.json --exclude "*.test.js" --exclude "**/__tests__/*"

echo "==> Done: ${OUTPUT} ($(du -sh "${OUTPUT}" | cut -f1))"
