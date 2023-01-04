#!/bin/bash
# Calls the Cloud Run pipeline Runner service to submit
# a PipelineJob to Vertex AI. This script should run from
# the main directory. Change directory in case this is not the script root.

PIPELINE_RUNNER_SVC_URL=`gcloud run services describe run-pipeline --platform managed --region us-central1 --format 'value(status.url)'`
curl -v --ipv4 --http1.1 --trace-ascii - $PIPELINE_RUNNER_SVC_URL \
  -X POST \
  -H "Authorization:bearer $(gcloud auth print-identity-token --quiet)" \
  -H "Content-Type: application/json" \
  --data @pipelines/runtime_parameters/pipeline_parameter_values.json
