#!/bin/bash
# Creates a pipeline schedule.
# This script should run from the AutoMLOps/ directory
# Change directory in case this is not the script root.

PROJECT_ID=sandbox-srastatter
PARAMS_PATH=pipelines/runtime_parameters/pipeline_parameter_values.json
SERVICE_ACCOUNT_FULL=vertex-pipelines@sandbox-srastatter.iam.gserviceaccount.com
CLOUD_SOURCE_REPO=AutoMLOps-repo
PIPELINE_RUNNER_SVC_URL=`gcloud run services describe run-pipeline --platform managed --region us-central1 --format 'value(status.url)'`
CLOUD_SCHEDULE="0 */12 * * *"
CLOUD_SCHEDULE_LOCATION=us-central1

# Create cloud scheduler
if ! (gcloud scheduler jobs list --project="$PROJECT_ID" --location="$CLOUD_SCHEDULE_LOCATION" | grep --fixed-strings "AutoMLOps-schedule") && [ -n "$PIPELINE_RUNNER_SVC_URL" ]; then

  gcloud scheduler jobs create http AutoMLOps-schedule \
  --schedule="$CLOUD_SCHEDULE" \
  --uri=$PIPELINE_RUNNER_SVC_URL \
  --http-method=POST \
  --location=$CLOUD_SCHEDULE_LOCATION \
  --description="AutoMLOps cloud scheduled run." \
  --message-body-from-file=$PARAMS_PATH \
  --headers Content-Type=application/json,User-Agent=Google-Cloud-Scheduler \
  --oidc-service-account-email=$SERVICE_ACCOUNT_FULL

else

  echo "Cloud Scheduler AutoMLOps resource already exists in project $PROJECT_ID or Cloud Runner service not found"

fi
