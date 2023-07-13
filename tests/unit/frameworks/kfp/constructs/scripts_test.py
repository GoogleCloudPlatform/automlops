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

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=protected-access

import mock
import pytest
import pytest_mock

from AutoMLOps.frameworks.kfp.constructs.scripts import KfpScripts
import AutoMLOps.utils.constants
from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    LEFT_BRACKET,
    NEWLINE,
    RIGHT_BRACKET
)

@pytest.mark.parametrize(
    '''af_registry_location, af_registry_name, base_image, cb_trigger_location,'''
    '''cb_trigger_name, cloud_run_location, cloud_run_name, cloud_tasks_queue_location,'''
    '''cloud_tasks_queue_name, csr_branch_name, csr_name, gs_bucket_location,'''
    '''gs_bucket_name, pipeline_runner_sa, project_id, run_local, schedule_location,'''
    '''schedule_name, schedule_pattern, base_dir, vpc_connector, reqs''',
    [
        (
            'us-central1', 'my-registry', 'us-central1', 'gcr.io/my-project/my-image',
            'my-trigger', 'us-central1', 'my-run', 'us-central1',
            'my-queue', 'main', 'my-repo', 'us-central1',
            'my-bucket', 'my-service-account@serviceaccount.com', 'my-project', False, 'us-central1',
            'my-schedule', '0 12 * * *', 'base_dir', 'my-connector', ['pandas', 'kfp<2.0.0']
        ),
        (
            'us-central2', 'my-123registry', 'us-central1', 'gcr.io/my-project/my-image',
            'my-trigger', 'us-central1', 'my-run', 'us-central1',
            'my-queue', 'main', 'my-repo', 'us-central3',
            'my-bucket', 'my-service-account@serviceaccount.com', 'my-project', False, 'us-central1',
            'my-schedule', '0 10 * * *', 'base_dir', 'my-connector', ['numpy', 'kfp<2.0.0']
        )
    ]
)
def test_init(mocker: pytest_mock.MockerFixture,
              tmpdir: pytest.FixtureRequest,
              af_registry_location: str,
              af_registry_name: str,
              base_image: str,
              cb_trigger_location: str,
              cb_trigger_name: str,
              cloud_run_location: str,
              cloud_run_name: str,
              cloud_tasks_queue_location: str,
              cloud_tasks_queue_name: str,
              csr_branch_name: str,
              csr_name: str,
              gs_bucket_location: str,
              gs_bucket_name: str,
              pipeline_runner_sa: str,
              project_id: str,
              run_local: bool,
              schedule_location: str,
              schedule_name: str,
              schedule_pattern: str,
              base_dir: str,
              vpc_connector: str,
              reqs: list):
    """Tests the initialization of the KFPScripts class.

    Args:
        mocker: Mocker used to patch constants to test in tempoarary environment.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.
        af_registry_location (str): Region of the Artifact Registry.
        af_registry_name (str): Artifact Registry name where components are stored.
        base_image (str): The image to use in the dockerfile.
        cb_trigger_location (str): The location of the cloudbuild trigger.
        cb_trigger_name (str): The name of the cloudbuild trigger.
        cloud_run_location (str): The location of the cloud runner service.
        cloud_run_name (str): The name of the cloud runner service.
        cloud_tasks_queue_location (str): The location of the cloud tasks queue.
        cloud_tasks_queue_name (str): The name of the cloud tasks queue.
        csr_branch_name (str): The name of the csr branch to push to to trigger cb job.
        csr_name (str): The name of the cloud source repo to use.
        gs_bucket_location (str): Region of the GS bucket.
        gs_bucket_name (str): GS bucket name where pipeline run metadata is stored.
        pipeline_runner_sa (str): Service Account to runner PipelineJobs.
        project_id (str): The project ID.
        run_local (bool): Flag that determines whether to use Cloud Run CI/CD.
        schedule_location (str): The location of the scheduler resource.
        schedule_name (str): The name of the scheduler resource.
        schedule_pattern (str): Cron formatted value used to create a scheduled retrain job.
        base_dir (str): Top directory name.
        vpc_connector (str): The name of the vpc connector to use.
        reqs (list): Package requirements to write into requirements.txt
    """

    # Patch global directory variables
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts,
                        'GENERATED_COMPONENT_BASE',
                        tmpdir)
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts,
                        'GENERATED_PARAMETER_VALUES_PATH',
                        tmpdir)
    mocker.patch.object(AutoMLOps.frameworks.kfp.constructs.scripts,
                        'GENERATED_PIPELINE_JOB_SPEC_PATH',
                        tmpdir)
    mocker.patch.object(AutoMLOps.utils.utils,
                        'CACHE_DIR',
                        '.')

    # Create requirements file
    with open(file=f'{tmpdir}/requirements.txt', mode='w', encoding='utf-8') as f:
        f.write(''.join(r+'\n' for r in reqs))

    # Create scripts object
    with mock.patch('AutoMLOps.frameworks.kfp.constructs.scripts.execute_process',
                    return_value=''):
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
            f'  parameter_values_path: {tmpdir}\n'
            f'  pipeline_component_directory: components\n'
            f'  pipeline_job_spec_path: {tmpdir}\n'
            f'  pipeline_region: {gs_bucket_location}\n'
            f'  pipeline_storage_path: gs://{gs_bucket_name}/pipeline_root\n')

        default_reqs = [
            'google-cloud-aiplatform',
            'google-cloud-appengine-logging',
            'google-cloud-audit-log',
            'google-cloud-bigquery',
            'google-cloud-bigquery-storage',
            'google-cloud-bigtable',
            'google-cloud-core',
            'google-cloud-dataproc',
            'google-cloud-datastore',
            'google-cloud-dlp',
            'google-cloud-firestore',
            'google-cloud-kms',
            'google-cloud-language',
            'google-cloud-logging',
            'google-cloud-monitoring',
            'google-cloud-notebooks',
            'google-cloud-pipeline-components',
            'google-cloud-pubsub',
            'google-cloud-pubsublite',
            'google-cloud-recommendations-ai',
            'google-cloud-resource-manager',
            'google-cloud-scheduler',
            'google-cloud-spanner',
            'google-cloud-speech',
            'google-cloud-storage',
            'google-cloud-tasks',
            'google-cloud-translate',
            'google-cloud-videointelligence',
            'google-cloud-vision',
            'db_dtypes',
            'pyarrow',
            'gcsfs',
            'fsspec'
        ]
        assert scripts.requirements == f'{"".join(r+f"{NEWLINE}" for r in sorted(reqs + default_reqs))}'
