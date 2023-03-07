#!/bin/bash
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# DISCLAIMER: This code is generated as part of the AutoMLOps output.

# This script will create an artifact registry and gs bucket if they do not already exist.

GREEN='[0;32m'
NC='[0m'
AF_REGISTRY_NAME=vertex-mlops-af
AF_REGISTRY_LOCATION=us-central1
PROJECT_ID=automlops-sandbox
PROJECT_NUMBER=`gcloud projects describe automlops-sandbox --format 'value(projectNumber)'`
BUCKET_NAME=automlops-sandbox-bucket
BUCKET_LOCATION=us-central1
SERVICE_ACCOUNT_NAME=vertex-pipelines
SERVICE_ACCOUNT_FULL=vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com
CLOUD_SOURCE_REPO=AutoMLOps-repo
CLOUD_SOURCE_REPO_BRANCH=automlops
CB_TRIGGER_LOCATION=us-central1
CB_TRIGGER_NAME=automlops-trigger
CLOUD_TASKS_QUEUE_LOCATION=us-central1
CLOUD_TASKS_QUEUE_NAME=queueing-svc

echo -e "$GREEN Updating required API services in project $PROJECT_ID $NC"
gcloud services enable cloudresourcemanager.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudtasks.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  ml.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  sourcerepo.googleapis.com

echo -e "$GREEN Checking for Artifact Registry: $AF_REGISTRY_NAME in project $PROJECT_ID $NC"
if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "(^|[[:blank:]])$AF_REGISTRY_NAME($|[[:blank:]]))"; then

  echo "Creating Artifact Registry: ${AF_REGISTRY_NAME} in project $PROJECT_ID"
  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \
    --repository-format=docker \
    --location=$AF_REGISTRY_LOCATION \
    --project="$PROJECT_ID" \
    --description="Artifact Registry ${AF_REGISTRY_NAME} in ${AF_REGISTRY_LOCATION}." 

else

  echo "Artifact Registry: ${AF_REGISTRY_NAME} already exists in project $PROJECT_ID"

fi


echo -e "$GREEN Checking for GS Bucket: $BUCKET_NAME in project $PROJECT_ID $NC"
if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "(^|[[:blank:]])$BUCKET_NAME($|[[:blank:]]))"; then

  echo "Creating GS Bucket: ${BUCKET_NAME} in project $PROJECT_ID"
  gsutil mb -l ${BUCKET_LOCATION} gs://$BUCKET_NAME

else

  echo "GS Bucket: ${BUCKET_NAME} already exists in project $PROJECT_ID"

fi

echo -e "$GREEN Checking for Service Account: $SERVICE_ACCOUNT_NAME in project $PROJECT_ID $NC"
if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep --fixed-strings "(^|[[:blank:]])$SERVICE_ACCOUNT_FULL($|[[:blank:]]))"; then

  echo "Creating Service Account: ${SERVICE_ACCOUNT_NAME} in project $PROJECT_ID"
  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
      --description="For submitting PipelineJobs" \
      --display-name="Pipeline Runner Service Account"
else

  echo "Service Account: ${SERVICE_ACCOUNT_NAME} already exists in project $PROJECT_ID"

fi

echo -e "$GREEN Updating required IAM roles in project $PROJECT_ID $NC"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/aiplatform.user" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/artifactregistry.reader" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/bigquery.user" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
   --role="roles/bigquery.dataEditor" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/iam.serviceAccountUser" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/storage.admin" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \
    --role="roles/run.admin" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/cloudtasks.enqueuer" \
    --no-user-output-enabled

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
    --role="roles/cloudscheduler.admin" \
    --no-user-output-enabled

echo -e "$GREEN Checking for Cloud Source Repository: $CLOUD_SOURCE_REPO in project $PROJECT_ID $NC"
if ! (gcloud source repos list --project="$PROJECT_ID" | grep --fixed-strings "(^|[[:blank:]])$CLOUD_SOURCE_REPO($|[[:blank:]]))"; then

  echo "Creating Cloud Source Repository: ${CLOUD_SOURCE_REPO} in project $PROJECT_ID"
  gcloud source repos create $CLOUD_SOURCE_REPO

else

  echo "Cloud Source Repository: ${CLOUD_SOURCE_REPO} already exists in project $PROJECT_ID"

fi

# Create cloud tasks queue
echo -e "$GREEN Checking for Cloud Tasks Queue: $CLOUD_TASKS_QUEUE_NAME in project $PROJECT_ID $NC"
if ! (gcloud tasks queues list --location $CLOUD_TASKS_QUEUE_LOCATION | grep --fixed-strings "(^|[[:blank:]])$CLOUD_TASKS_QUEUE_NAME($|[[:blank:]]))"; then

  echo "Creating Cloud Tasks Queue: ${CLOUD_TASKS_QUEUE_NAME} in project $PROJECT_ID"
  gcloud tasks queues create $CLOUD_TASKS_QUEUE_NAME \
  --location=$CLOUD_TASKS_QUEUE_LOCATION

else

  echo "Cloud Tasks Queue: ${CLOUD_TASKS_QUEUE_NAME} already exists in project $PROJECT_ID"

fi

# Create cloud build trigger
echo -e "$GREEN Checking for Cloudbuild Trigger: $CB_TRIGGER_NAME in project $PROJECT_ID $NC"
if ! (gcloud beta builds triggers list --project="$PROJECT_ID" --region="$CB_TRIGGER_LOCATION" | grep --fixed-strings "(^|[[:blank:]])name: $CB_TRIGGER_NAME($|[[:blank:]]))"; then

  echo "Creating Cloudbuild Trigger on branch $CLOUD_SOURCE_REPO_BRANCH in project $PROJECT_ID for repo ${CLOUD_SOURCE_REPO}"
  gcloud beta builds triggers create cloud-source-repositories \
  --region=$CB_TRIGGER_LOCATION \
  --name=$CB_TRIGGER_NAME \
  --repo=$CLOUD_SOURCE_REPO \
  --branch-pattern="$CLOUD_SOURCE_REPO_BRANCH" \
  --build-config=AutoMLOps/cloudbuild.yaml

else

  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${CLOUD_SOURCE_REPO}"

fi
