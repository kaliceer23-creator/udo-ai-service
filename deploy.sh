#!/usr/bin/env bash
set -e

# UDO AI Service - Google Cloud Run Deployment Script
# Deploys the service in asia-southeast1 (Singapore) with autoscaling to 0 when idle.

# Ensure gcloud is in PATH if installed in user home
if ! command -v gcloud &> /dev/null && [ -f "$HOME/google-cloud-sdk/bin/gcloud" ]; then
  export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# Ensure Python 3.10+ is used if system default is 3.9
if [ -x "/opt/homebrew/bin/python3.11" ]; then
  export CLOUDSDK_PYTHON="/opt/homebrew/bin/python3.11"
fi

SERVICE_NAME="udo-ai-service"
REGION="asia-southeast1"

echo "Deploying ${SERVICE_NAME} to Google Cloud Run..."

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 4 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 30s

echo "Deployment process finished."
