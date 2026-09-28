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
  --service-account "captrans-translator@project-de5847cd-022d-40ca-ad7.iam.gserviceaccount.com" \
  --min-instances 0 \
  --max-instances 4 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60s \
  --set-env-vars "GCP_PROJECT=project-de5847cd-022d-40ca-ad7,VERTEX_LOCATION=global,GOOGLE_GENAI_USE_ENTERPRISE=True,GEMINI_MODEL=gemini-2.0-flash" \
  --quiet

echo "Deployment process finished."
