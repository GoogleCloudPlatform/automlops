#!/bin/bash
# This script will create an artifact registry and gs bucket if they do not already exist.

AF_REGISTRY_NAME=vertex-mlops-af
AF_REGISTRY_LOCATION=us-central1
PROJECT_ID=sandbox-srastatter
BUCKET_NAME=sandbox-srastatter-bucket
BUCKET_LOCATION=us-central1
SERVICE_ACCOUNT_NAME=vertex-pipelines
SERVICE_ACCOUNT_FULL=vertex-pipelines@sandbox-srastatter.iam.gserviceaccount.com
CLOUD_SOURCE_REPO=AutoMLOps-repo

if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "$AF_REGISTRY_NAME"); then

  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \
    --repository-format=docker \
    --location=$AF_REGISTRY_LOCATION \
    --project="$PROJECT_ID" \
    --description="Artifact Registry ${AF_REGISTRY_NAME} in ${AF_REGISTRY_LOCATION}." 
else

  echo "Artifact Registry: ${AF_REGISTRY_NAME} already exists in project $PROJECT_ID"

fi


if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then

  gsutil mb -l ${BUCKET_LOCATION} gs://$BUCKET_NAME

else

  echo "GS Bucket: ${BUCKET_NAME} already exists in project $PROJECT_ID"

fi

if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep --fixed-strings "$SERVICE_ACCOUNT_FULL"); then

  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
      --description="For submitting PipelineJobs" \
      --display-name="Pipeline Runner Service Account"
else

  echo "Service Account: ${SERVICE_ACCOUNT_NAME} already exists in project $PROJECT_ID"

fi
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/aiplatform.user" 

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/artifactregistry.reader" 

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/bigquery.user" 

gcloud projects add-iam-policy-binding $PROJECT_ID \
   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
   --role="roles/bigquery.dataEditor" 

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/iam.serviceAccountUser" 

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/storage.admin"

# Create source repo
if ! (gcloud source repos list --project="$PROJECT_ID" | grep --fixed-strings "$CLOUD_SOURCE_REPO"); then

  gcloud source repos create $CLOUD_SOURCE_REPO

else

  echo "Cloud Source Repository: ${CLOUD_SOURCE_REPO} already exists in project $PROJECT_ID"

fi

if ! (ls -a | grep $CLOUD_SOURCE_REPO); then

  gcloud source repos clone $CLOUD_SOURCE_REPO --project=$PROJECT_ID

else

  echo "Directory path specified exists and is not empty"

fi

# Create cloud build trigger
# Account needs to have Cloud Build Editor
if ! (gcloud beta builds triggers list --project="$PROJECT_ID" | grep --fixed-strings "$CLOUD_SOURCE_REPO" && gcloud beta builds triggers list --project="$PROJECT_ID" | grep --fixed-strings "AutoMLOps/cloudbuild.yaml"); then

  gcloud beta builds triggers create cloud-source-repositories \
  --repo=$CLOUD_SOURCE_REPO \
  --branch-pattern=main \
  --build-config=AutoMLOps/cloudbuild.yaml

else

  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${CLOUD_SOURCE_REPO}"

fi
