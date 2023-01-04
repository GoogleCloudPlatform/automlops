#!/bin/bash
# Submits a Cloud Build job that builds and deploys the components
# This script should run from the AutoMLOps/ directory
# Change directory in case this is not the script root.

gcloud builds submit .. --config cloudbuild.yaml --timeout=3600
