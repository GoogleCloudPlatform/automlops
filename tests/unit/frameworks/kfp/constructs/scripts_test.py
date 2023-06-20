# Copyright 2023 Google LLC. All Rights Reserved.
#
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

from mock import patch
import mock
import pytest
import os
import AutoMLOps.utils.constants
from AutoMLOps.frameworks.kfp.constructs.scripts import KfpScripts
from AutoMLOps.utils.utils import execute_process
from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    NEWLINE,
    LEFT_BRACKET,
    RIGHT_BRACKET,
    GENERATED_COMPONENT_BASE,
    CACHE_DIR,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_JOB_SPEC_PATH
)

@pytest.mark.parametrize(
    '''af_registry_location, af_registry_name, base_image, cb_trigger_location, cb_trigger_name, cloud_run_location, cloud_run_name,'''
    '''cloud_tasks_queue_location, cloud_tasks_queue_name, csr_branch_name, csr_name, gs_bucket_location, gs_bucket_name, pipeline_runner_sa,'''
    '''project_id, run_local, schedule_location, schedule_name, schedule_pattern, base_dir, vpc_connector, reqs''',
    [
        (
            'us-central1', 'my-registry', 'us-central1', 'gcr.io/my-project/my-image', 'my-trigger', 'us-central1', 'my-run',
            'us-central1', 'my-queue', 'main', 'my-repo', 'us-central1', 'my-bucket', 'my-service-account@serviceaccount.com',
            'my-project', False, 'us-central1', 'my-schedule', '0 12 * * *', 'base_dir', 'my-connector', ['req1', 'req2']
        )
    ]
)
def test_init(mocker,
              af_registry_location,
              af_registry_name,
              base_image,
              cb_trigger_location,
              cb_trigger_name,
              cloud_run_location,
              cloud_run_name,
              cloud_tasks_queue_location,
              cloud_tasks_queue_name,
              csr_branch_name,
              csr_name,
              gs_bucket_location,
              gs_bucket_name,
              pipeline_runner_sa,
              project_id,
              run_local,
              schedule_location,
              schedule_name,
              schedule_pattern,
              base_dir,
              vpc_connector,
              reqs):
    """Tests the initialization of the KFPScripts class."""

    # Patch global directory variables
    temp_dir = 'test_temp_dir'
    os.makedirs(temp_dir)
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts, 'GENERATED_COMPONENT_BASE', temp_dir)
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts, 'GENERATED_PARAMETER_VALUES_PATH', temp_dir)
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts, 'GENERATED_PIPELINE_JOB_SPEC_PATH', temp_dir)
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')

    # Create requirements file
    with open('test_temp_dir/requirements.txt', 'w') as f:
        f.write(''.join(r+'\n' for r in reqs))

    # Create scripts object
    with mock.patch('AutoMLOps.frameworks.kfp.constructs.scripts.execute_process', return_value=''):
        scripts = KfpScripts(
            af_registry_location=af_registry_location,
            af_registry_name=af_registry_name,
            base_image=base_image,
            cb_trigger_location=cb_trigger_location,
            cb_trigger_name=cb_trigger_name,
            cloud_run_location=cloud_run_location,
            cloud_run_name=cloud_run_name,
            cloud_tasks_queue_location=cloud_tasks_queue_location,
            cloud_tasks_queue_name=cloud_tasks_queue_name,
            csr_branch_name=csr_branch_name,
            csr_name=csr_name,
            gs_bucket_location=gs_bucket_location,
            gs_bucket_name=gs_bucket_name,
            pipeline_runner_sa=pipeline_runner_sa,
            project_id=project_id,
            run_local=run_local,
            schedule_location=schedule_location,
            schedule_name=schedule_name,
            schedule_pattern=schedule_pattern,
            base_dir=base_dir,
            vpc_connector=vpc_connector,
        )

        # Assert object properties were created properly
        assert scripts._af_registry_location == af_registry_location
        assert scripts._af_registry_name == af_registry_name
        assert scripts._cb_trigger_location == cb_trigger_location
        assert scripts._cb_trigger_name == cb_trigger_name
        assert scripts._cloud_run_location == cloud_run_location
        assert scripts._cloud_run_name == cloud_run_name
        assert scripts._cloud_tasks_queue_location == cloud_tasks_queue_location
        assert scripts._cloud_tasks_queue_name == cloud_tasks_queue_name
        assert scripts._cloud_source_repository_branch == csr_branch_name
        assert scripts._cloud_source_repository == csr_name
        assert scripts._base_image == base_image
        assert scripts._gs_bucket_location == gs_bucket_location
        assert scripts._gs_bucket_name == gs_bucket_name
        assert scripts._pipeline_runner_service_account == pipeline_runner_sa
        assert scripts._project_id == project_id
        assert scripts._run_local == run_local
        assert scripts._cloud_schedule_location == schedule_location
        assert scripts._cloud_schedule_name == schedule_name
        assert scripts._cloud_schedule_pattern == schedule_pattern
        assert scripts._base_dir == base_dir
        assert scripts._vpc_connector == vpc_connector

        assert scripts.build_pipeline_spec == (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Builds the pipeline specs\n'
            f'# This script should run from the {base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline --config $CONFIG_FILE\n')

        assert scripts.build_components == (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Submits a Cloud Build job that builds and deploys the components\n'
            f'# This script should run from the {base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n')

        assert scripts.run_pipeline == (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Submits the PipelineJob to Vertex AI\n'
            f'# This script should run from the {base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE\n')

        assert scripts.run_all == (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Builds components, pipeline specs, and submits the PipelineJob.\n'
            f'# This script should run from the {base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            '''GREEN='\033[0;32m'\n'''
            '''NC='\033[0m'\n'''
            '\n'
            'echo -e "${GREEN} BUILDING COMPONENTS ${NC}"\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n'
            '\n'
            'echo -e "${GREEN} BUILDING PIPELINE SPEC ${NC}"\n'
            './scripts/build_pipeline_spec.sh\n'
            '\n'
            'echo -e "${GREEN} RUNNING PIPELINE JOB ${NC}"\n'
            './scripts/run_pipeline.sh\n')

        assert scripts.create_resources_script == (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
            f'\n'
            f'''GREEN='\033[0;32m'\n'''
            f'''NC='\033[0m'\n'''
            f'''AF_REGISTRY_NAME={af_registry_name}\n'''
            f'''AF_REGISTRY_LOCATION={af_registry_location}\n'''
            f'''PROJECT_ID={project_id}\n'''
            f'''PROJECT_NUMBER=`gcloud projects describe {project_id} --format 'value(projectNumber)'`\n'''
            f'''BUCKET_NAME={gs_bucket_name}\n'''
            f'''BUCKET_LOCATION={gs_bucket_location}\n'''
            f'''SERVICE_ACCOUNT_NAME={pipeline_runner_sa.split('@')[0]}\n'''
            f'''SERVICE_ACCOUNT_FULL={pipeline_runner_sa}\n'''
            f'''CLOUD_SOURCE_REPO={csr_name}\n'''
            f'''CLOUD_SOURCE_REPO_BRANCH={csr_branch_name}\n'''
            f'''CB_TRIGGER_LOCATION={cb_trigger_location}\n'''
            f'''CB_TRIGGER_NAME={cb_trigger_name}\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION={cloud_tasks_queue_location}\n'''
            f'''CLOUD_TASKS_QUEUE_NAME={cloud_tasks_queue_name}\n'''
            f'\n'
            f'echo -e "$GREEN Updating required API services in project $PROJECT_ID $NC"\n'
            f'gcloud services enable cloudresourcemanager.googleapis.com \{NEWLINE}'
            f'  aiplatform.googleapis.com \{NEWLINE}'
            f'  artifactregistry.googleapis.com \{NEWLINE}'
            f'  cloudbuild.googleapis.com \{NEWLINE}'
            f'  cloudscheduler.googleapis.com \{NEWLINE}'
            f'  cloudtasks.googleapis.com \{NEWLINE}'
            f'  compute.googleapis.com \{NEWLINE}'
            f'  iam.googleapis.com \{NEWLINE}'
            f'  iamcredentials.googleapis.com \{NEWLINE}'
            f'  ml.googleapis.com \{NEWLINE}'
            f'  run.googleapis.com \{NEWLINE}'
            f'  storage.googleapis.com \{NEWLINE}'
            f'  sourcerepo.googleapis.com\n'
            f'\n'
            f'echo -e "$GREEN Checking for Artifact Registry: $AF_REGISTRY_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep -E "(^|[[:blank:]])$AF_REGISTRY_NAME($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Artifact Registry: ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \{NEWLINE}'
            f'    --repository-format=docker \{NEWLINE}'
            f'    --location=$AF_REGISTRY_LOCATION \{NEWLINE}'
            f'    --project="$PROJECT_ID" \{NEWLINE}'
            f'    --description="Artifact Registry ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} in ${LEFT_BRACKET}AF_REGISTRY_LOCATION{RIGHT_BRACKET}." \n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Artifact Registry: ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'\n'
            f'echo -e "$GREEN Checking for GS Bucket: $BUCKET_NAME in project $PROJECT_ID $NC"\n'
            f'if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then\n'
            f'\n'
            f'  echo "Creating GS Bucket: ${LEFT_BRACKET}BUCKET_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gsutil mb -l ${LEFT_BRACKET}BUCKET_LOCATION{RIGHT_BRACKET} gs://$BUCKET_NAME\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "GS Bucket: ${LEFT_BRACKET}BUCKET_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'echo -e "$GREEN Checking for Service Account: $SERVICE_ACCOUNT_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep -E "(^|[[:blank:]])$SERVICE_ACCOUNT_FULL($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Service Account: ${LEFT_BRACKET}SERVICE_ACCOUNT_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \{NEWLINE}'
            f'      --description="For submitting PipelineJobs" \{NEWLINE}'
            f'      --display-name="Pipeline Runner Service Account"\n'
            f'else\n'
            f'\n'
            f'  echo "Service Account: ${LEFT_BRACKET}SERVICE_ACCOUNT_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'echo -e "$GREEN Updating required IAM roles in project $PROJECT_ID $NC"\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/aiplatform.user" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/artifactregistry.reader" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/bigquery.user" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'   --role="roles/bigquery.dataEditor" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/iam.serviceAccountUser" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/storage.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/run.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/run.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/iam.serviceAccountUser" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/cloudtasks.enqueuer" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/cloudscheduler.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'echo -e "$GREEN Checking for Cloud Source Repository: $CLOUD_SOURCE_REPO in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud source repos list --project="$PROJECT_ID" | grep -E "(^|[[:blank:]])$CLOUD_SOURCE_REPO($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Cloud Source Repository: ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud source repos create $CLOUD_SOURCE_REPO\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloud Source Repository: ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'# Create cloud tasks queue\n'
            f'echo -e "$GREEN Checking for Cloud Tasks Queue: $CLOUD_TASKS_QUEUE_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud tasks queues list --location $CLOUD_TASKS_QUEUE_LOCATION | grep -E "(^|[[:blank:]])$CLOUD_TASKS_QUEUE_NAME($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Cloud Tasks Queue: ${LEFT_BRACKET}CLOUD_TASKS_QUEUE_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud tasks queues create $CLOUD_TASKS_QUEUE_NAME \{NEWLINE}'
            f'  --location=$CLOUD_TASKS_QUEUE_LOCATION\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloud Tasks Queue: ${LEFT_BRACKET}CLOUD_TASKS_QUEUE_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'# Create cloud build trigger\n'
            f'echo -e "$GREEN Checking for Cloudbuild Trigger: $CB_TRIGGER_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud beta builds triggers list --project="$PROJECT_ID" --region="$CB_TRIGGER_LOCATION" | grep -E "(^|[[:blank:]])name: $CB_TRIGGER_NAME($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Cloudbuild Trigger on branch $CLOUD_SOURCE_REPO_BRANCH in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
            f'  gcloud beta builds triggers create cloud-source-repositories \{NEWLINE}'
            f'  --region=$CB_TRIGGER_LOCATION \{NEWLINE}'
            f'  --name=$CB_TRIGGER_NAME \{NEWLINE}'
            f'  --repo=$CLOUD_SOURCE_REPO \{NEWLINE}'
            f'  --branch-pattern="$CLOUD_SOURCE_REPO_BRANCH" \{NEWLINE}'
            f'  --build-config=base_dircloudbuild.yaml\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
            f'\n'
            f'fi\n')

        assert scripts.dockerfile == (
            GENERATED_LICENSE +
            f'FROM {base_image}\n'
            f'RUN python -m pip install --upgrade pip\n'
            f'COPY requirements.txt .\n'
            f'RUN python -m pip install -r \ \n'
            f'    requirements.txt --quiet --no-cache-dir \ \n'
            f'    && rm -f requirements.txt\n'
            f'COPY ./src /pipelines/component/src\n'
            f'ENTRYPOINT ["/bin/bash"]\n')

        assert scripts.defaults == (
            GENERATED_LICENSE +
            f'# These values are descriptive only - do not change.\n'
            f'# Rerun AutoMLOps.generate() to change these values.\n'
            f'gcp:\n'
            f'  af_registry_location: {af_registry_location}\n'
            f'  af_registry_name: {af_registry_name}\n'
            f'  base_image: {base_image}\n'
            f'  cb_trigger_location: {cb_trigger_location}\n'
            f'  cb_trigger_name: {cb_trigger_name}\n'
            f'  cloud_run_location: {cloud_run_location}\n'
            f'  cloud_run_name: {cloud_run_name}\n'
            f'  cloud_tasks_queue_location: {cloud_tasks_queue_location}\n'
            f'  cloud_tasks_queue_name: {cloud_tasks_queue_name}\n'
            f'  cloud_schedule_location: {schedule_location}\n'
            f'  cloud_schedule_name: {schedule_name}\n'
            f'  cloud_schedule_pattern: {schedule_pattern}\n'
            f'  cloud_source_repository: {csr_name}\n'
            f'  cloud_source_repository_branch: {csr_branch_name}\n'
            f'  gs_bucket_name: {gs_bucket_name}\n'
            f'  pipeline_runner_service_account: {pipeline_runner_sa}\n'
            f'  project_id: {project_id}\n'
            f'  vpc_connector: {vpc_connector}\n'
            f'\n'
            f'pipelines:\n'
            f'  parameter_values_path: {temp_dir}\n'
            f'  pipeline_component_directory: components\n'
            f'  pipeline_job_spec_path: {temp_dir}\n'
            f'  pipeline_region: {gs_bucket_location}\n'
            f'  pipeline_storage_path: gs://{gs_bucket_name}/pipeline_root\n')

        assert scripts.requirements == (
            f'db_dtypes\n'
            f'fsspec\n'
            f'gcsfs\n'
            f'google-cloud-aiplatform\n'
            f'google-cloud-appengine-logging\n'
            f'google-cloud-audit-log\n'
            f'google-cloud-bigquery\n'
            f'google-cloud-bigquery-storage\n'
            f'google-cloud-bigtable\n'
            f'google-cloud-core\n'
            f'google-cloud-dataproc\n'
            f'google-cloud-datastore\n'
            f'google-cloud-dlp\n'
            f'google-cloud-firestore\n'
            f'google-cloud-kms\n'
            f'google-cloud-language\n'
            f'google-cloud-logging\n'
            f'google-cloud-monitoring\n'
            f'google-cloud-notebooks\n'
            f'google-cloud-pipeline-components\n'
            f'google-cloud-pubsub\n'
            f'google-cloud-pubsublite\n'
            f'google-cloud-recommendations-ai\n'
            f'google-cloud-resource-manager\n'
            f'google-cloud-scheduler\n'
            f'google-cloud-spanner\n'
            f'google-cloud-speech\n'
            f'google-cloud-storage\n'
            f'google-cloud-tasks\n'
            f'google-cloud-translate\n'
            f'google-cloud-videointelligence\n'
            f'google-cloud-vision\n'
            f'pyarrow\n'
            f'{"".join(r+f"{NEWLINE}" for r in sorted(reqs))}')

    # Remove temporary files
    os.remove('test_temp_dir/requirements.txt')
    os.rmdir('test_temp_dir')