#!/bin/bash
#
# Helper script to configure gcloud in Github Actions context
set -euxo pipefail

unset CLOUDSDK_CORE_PROJECT
unset CLOUDSDK_PROJECT
unset GCLOUD_PROJECT
unset GCP_PROJECT
unset GOOGLE_CLOUD_PROJECT

gcloud config set project "$1"

gcloud components install beta

echo "gcloud configured"
