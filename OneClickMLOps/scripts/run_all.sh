#! /bin/bash
# Builds components, pipeline specs, and submits the PipelineJob.
# This script should run from the main directory
# Change directory in case this isn't the script root.

GREEN='[0;32m'
NC='[0m'

echo -e "${GREEN} BUILDING COMPONENTS ${NC}"
gcloud builds submit .. --config cloudbuild.yaml --timeout=3600

echo -e "${GREEN} BUILDING PIPELINE SPEC ${NC}"
./scripts/build_pipeline_spec.sh

echo -e "${GREEN} RUNNING PIPELINE JOB ${NC}"
./scripts/run_pipeline.sh
