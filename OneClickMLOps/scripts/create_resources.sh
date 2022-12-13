#! /bin/bash
# This script will create an artifact registry and gs bucket if they do not already exist.

AF_REGISTRY_NAME=mlops-boxer-test
AF_REGISTRY_LOCATION=us-central1
PROJECT_ID=sandbox-srastatter
BUCKET_NAME=mlops-boxer-test
BUCKET_LOCATION=us-central1

if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "$AF_REGISTRY_NAME"); then

  gcloud artifacts repositories create "$AF_REGISTRY_NAME"     --repository-format=docker     --location=$AF_REGISTRY_LOCATION     --project="$PROJECT_ID"     --description="Artifact Registry ${AF_REGISTRY_NAME} in ${AF_REGISTRY_LOCATION}."
else

  echo "Artifact Registry: ${AF_REGISTRY_NAME} already exists in project $PROJECT_ID"

fi


if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then

  gsutil mb -l ${BUCKET_LOCATION} gs://$BUCKET_NAME

else

  echo "GS Bucket: ${BUCKET_NAME} already exists in project $PROJECT_ID"

fi
