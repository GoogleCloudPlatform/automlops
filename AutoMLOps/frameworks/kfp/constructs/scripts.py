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

"""Code strings for kfp scripts."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=line-too-long

import re

from AutoMLOps.utils.utils import (
    execute_process,
    get_components_list,
    read_file,
    read_yaml_file
)
from AutoMLOps.utils.constants import (
    GENERATED_COMPONENT_BASE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_JOB_SPEC_PATH,
    LEFT_BRACKET,
    NEWLINE,
    PINNED_KFP_VERSION,
    RIGHT_BRACKET
)

class KfpScripts():
    """Generates files related to running kubeflow pipelines."""
    def __init__(self,
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
                 run_local: str,
                 schedule_location: str,
                 schedule_name: str,
                 schedule_pattern: str,
                 base_dir: str,
                 vpc_connector: str):
        """Constructs scripts for resource deployment and running Kubeflow pipelines.

        Args:
            af_registry_location: Region of the Artifact Registry.
            af_registry_name: Artifact Registry name where components are stored.
            cb_trigger_location: The location of the cloudbuild trigger.
            cb_trigger_name: The name of the cloudbuild trigger.
            cloud_run_location: The location of the cloud runner service.
            cloud_run_name: The name of the cloud runner service.
            cloud_tasks_queue_location: The location of the cloud tasks queue.
            cloud_tasks_queue_name: The name of the cloud tasks queue.
            csr_branch_name: The name of the csr branch to push to to trigger cb job.
            csr_name: The name of the cloud source repo to use.
            base_image: The image to use in the dockerfile.
            gs_bucket_location: Region of the GS bucket.
            gs_bucket_name: GS bucket name where pipeline run metadata is stored.
            pipeline_runner_sa: Service Account to runner PipelineJobs.
            project_id: The project ID.
            run_local: Flag that determines whether to use Cloud Run CI/CD.
            schedule_location: The location of the scheduler resource.
            schedule_name: The name of the scheduler resource.
            schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
            base_dir: Top directory name.
            vpc_connector: The name of the vpc connector to use.
        """
        # Set passed variables as hidden attributes
        self._base_dir = base_dir
        self._run_local = run_local
        self._af_registry_name = af_registry_name
        self._af_registry_location = af_registry_location
        self._project_id = project_id
        self._gs_bucket_name = gs_bucket_name
        self._gs_bucket_location = gs_bucket_location
        self._pipeline_region = gs_bucket_location
        self._pipeline_runner_service_account = pipeline_runner_sa
        self._cloud_source_repository = csr_name
        self._cloud_source_repository_branch = csr_branch_name
        self._cb_trigger_location = cb_trigger_location
        self._cb_trigger_name = cb_trigger_name
        self._cloud_tasks_queue_location = cloud_tasks_queue_location
        self._cloud_tasks_queue_name = cloud_tasks_queue_name
        self._vpc_connector = vpc_connector
        self._cloud_run_name = cloud_run_name
        self._cloud_run_location = cloud_run_location
        self._cloud_schedule_location = schedule_location
        self._cloud_schedule_name = schedule_name
        self._cloud_schedule_pattern = schedule_pattern
        self._base_image = base_image

        # Set generated scripts as public attributes
        self.build_pipeline_spec = self._build_pipeline_spec()
        self.build_components = self._build_components()
        self.run_pipeline = self._run_pipeline()
        self.run_all = self._run_all()
        self.create_resources_script = self._create_resources_script()
        self.dockerfile = self._create_dockerfile()
        self.defaults = self._create_default_config()
        self.requirements = self._create_requirements()
        self.readme = self._create_generated_readme()

    def _build_pipeline_spec(self):
        """Builds content of a shell script to build the pipeline specs.

        Returns:
            str: Text of script to build pipeline specs.
        """
        return (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Builds the pipeline specs\n'
            f'# This script should run from the {self._base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline --config $CONFIG_FILE\n')

    def _build_components(self):
        """Builds content of a shell script to build components.

        Returns:
            str: Text of script to build components.
        """
        return (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Submits a Cloud Build job that builds and deploys the components\n'
            f'# This script should run from the {self._base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n')

    def _run_pipeline(self):
        """Builds content of a shell script to run the pipeline.

        Returns:
            str: Text of script to run pipeline.
        """
        return (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Submits the PipelineJob to Vertex AI\n'
            f'# This script should run from the {self._base_dir} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE\n')

    def _run_all(self):
        """Builds content of a shell script to run all other shell scripts.

        Returns:
            str: Text of script to run all other scripts.
        """
        return (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            '# Builds components, pipeline specs, and submits the PipelineJob.\n'
            f'# This script should run from the {self._base_dir} directory\n'
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

    def _create_resources_script(self):
        """Builds content of create_resources.sh, which creates a specified
        artifact registry and gs bucket if they do not already exist. Also creates
        a service account to run Vertex AI Pipelines.

        Returns:
            str: Text to be written to create_resources.sh
        """
        create_resources_script = (
            '#!/bin/bash\n' + GENERATED_LICENSE +
            f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
            f'\n'
            f'''GREEN='\033[0;32m'\n'''
            f'''NC='\033[0m'\n'''
            f'''AF_REGISTRY_NAME={self._af_registry_name}\n'''
            f'''AF_REGISTRY_LOCATION={self._af_registry_location}\n'''
            f'''PROJECT_ID={self._project_id}\n'''
            f'''PROJECT_NUMBER=`gcloud projects describe {self._project_id} --format 'value(projectNumber)'`\n'''
            f'''BUCKET_NAME={self._gs_bucket_name}\n'''
            f'''BUCKET_LOCATION={self._pipeline_region}\n'''
            f'''SERVICE_ACCOUNT_NAME={self._pipeline_runner_service_account.split('@')[0]}\n'''
            f'''SERVICE_ACCOUNT_FULL={self._pipeline_runner_service_account}\n'''
            f'''CLOUD_SOURCE_REPO={self._cloud_source_repository}\n'''
            f'''CLOUD_SOURCE_REPO_BRANCH={self._cloud_source_repository_branch}\n'''
            f'''CB_TRIGGER_LOCATION={self._cb_trigger_location}\n'''
            f'''CB_TRIGGER_NAME={self._cb_trigger_name}\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION={self._cloud_tasks_queue_location}\n'''
            f'''CLOUD_TASKS_QUEUE_NAME={self._cloud_tasks_queue_name}\n'''
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
            f'fi\n')

        if not self._run_local:
            create_resources_script += (
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
                f'  --build-config={self._base_dir}cloudbuild.yaml\n'
                f'\n'
                f'else\n'
                f'\n'
                f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
                f'\n'
                f'fi\n')

        return create_resources_script

    def _create_dockerfile(self):
        """Creates the content of a Dockerfile to be written to the component_base directory.

        Returns:
            str: Text content of dockerfile.
        """
        return (
            GENERATED_LICENSE +
            f'FROM {self._base_image}\n'
            f'RUN python -m pip install --upgrade pip\n'
            f'COPY requirements.txt .\n'
            f'RUN python -m pip install -r \ \n'
            f'    requirements.txt --quiet --no-cache-dir \ \n'
            f'    && rm -f requirements.txt\n'
            f'COPY ./src /pipelines/component/src\n'
            f'ENTRYPOINT ["/bin/bash"]\n')

    def _create_default_config(self):
        """Creates defaults.yaml file contents. This defaults
        file is used by subsequent functions and by the pipeline
        files themselves.

        Returns:
            str: Defaults yaml file content
        """
        return (
            GENERATED_LICENSE +
            f'# These values are descriptive only - do not change.\n'
            f'# Rerun AutoMLOps.generate() to change these values.\n'
            f'gcp:\n'
            f'  af_registry_location: {self._af_registry_location}\n'
            f'  af_registry_name: {self._af_registry_name}\n'
            f'  base_image: {self._base_image}\n'
            f'  cb_trigger_location: {self._cb_trigger_location}\n'
            f'  cb_trigger_name: {self._cb_trigger_name}\n'
            f'  cloud_run_location: {self._cloud_run_location}\n'
            f'  cloud_run_name: {self._cloud_run_name}\n'
            f'  cloud_tasks_queue_location: {self._cloud_tasks_queue_location}\n'
            f'  cloud_tasks_queue_name: {self._cloud_tasks_queue_name}\n'
            f'  cloud_schedule_location: {self._cloud_schedule_location}\n'
            f'  cloud_schedule_name: {self._cloud_schedule_name}\n'
            f'  cloud_schedule_pattern: {self._cloud_schedule_pattern}\n'
            f'  cloud_source_repository: {self._cloud_source_repository}\n'
            f'  cloud_source_repository_branch: {self._cloud_source_repository_branch}\n'
            f'  gs_bucket_name: {self._gs_bucket_name}\n'
            f'  pipeline_runner_service_account: {self._pipeline_runner_service_account}\n'
            f'  project_id: {self._project_id}\n'
            f'  vpc_connector: {self._vpc_connector}\n'
            f'\n'
            f'pipelines:\n'
            f'  parameter_values_path: {GENERATED_PARAMETER_VALUES_PATH}\n'
            f'  pipeline_component_directory: components\n'
            f'  pipeline_job_spec_path: {GENERATED_PIPELINE_JOB_SPEC_PATH}\n'
            f'  pipeline_region: {self._gs_bucket_location}\n'
            f'  pipeline_storage_path: gs://{self._gs_bucket_name}/pipeline_root\n')

    def _create_requirements(self):
        """Writes a requirements.txt to the component_base directory.
        Infers pip requirements from the python srcfiles using 
        pipreqs. Takes user-inputted requirements, and addes some 
        default gcp packages as well as packages that are often missing
        in setup.py files (e.g db_types, pyarrow, gcsfs, fsspec).
        """
        reqs_filename = f'{GENERATED_COMPONENT_BASE}/requirements.txt'
        default_gcp_reqs = [
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
            'fsspec']
        # Infer reqs using pipreqs
        execute_process(f'python3 -m pipreqs.pipreqs {GENERATED_COMPONENT_BASE} --mode no-pin --force', to_null=False)
        pipreqs = read_file(reqs_filename).splitlines()
        # Get user-inputted requirements from the cache dir
        user_inp_reqs = []
        components_path_list = get_components_list()
        for component_path in components_path_list:
            component_spec = read_yaml_file(component_path)
            reqs = component_spec['implementation']['container']['command'][2]
            formatted_reqs = re.findall('\'([^\']*)\'', reqs)
            user_inp_reqs.extend(formatted_reqs)
        # Remove duplicates
        set_of_requirements = set(user_inp_reqs) if user_inp_reqs else set(pipreqs + default_gcp_reqs)
        # Remove empty string
        if '' in set_of_requirements:
            set_of_requirements.remove('')
        # Pin kfp version
        if 'kfp' in set_of_requirements:
            set_of_requirements.remove('kfp')
        set_of_requirements.add(PINNED_KFP_VERSION)
        # Stringify and sort
        reqs_str = ''.join(r+'\n' for r in sorted(set_of_requirements))
        return reqs_str

    def _create_generated_readme(self):
        """Creates a readme markdown file to describe the contents of the
        generated AutoMLOps code repo.

        Returns:
            str: readme.md file content
        """
        cloud_run_dirs = ''
        if not self._run_local:
            cloud_run_dirs = (
                '├── cloud_run                                      : Cloud Runner service for submitting PipelineJobs.\n'
                '    ├──run_pipeline                                : Contains main.py file, Dockerfile and requirements.txt\n'
                '    ├──queueing_svc                                : Contains files for scheduling and queueing jobs to runner service\n'
            )

        return (
            '# AutoMLOps - Generated Code Directory\n'
            '\n'
            '**Note: This directory contains code generated using AutoMLOps**\n'
            '\n'
            'AutoMLOps is a service that generates a production ready MLOps pipeline from Jupyter Notebooks, bridging the gap between Data Science and DevOps and accelerating the adoption and use of Vertex AI. The service generates an MLOps codebase for users to customize, and provides a way to build and manage a CI/CD integrated MLOps pipeline from the notebook. AutoMLOps automatically builds a source repo for versioning, cloudbuild configs and triggers, an artifact registry for storing custom components, gs buckets, service accounts and updated IAM privs for running pipelines, enables APIs (cloud Run, Cloud Build, Artifact Registry, etc.), creates a runner service API in Cloud Run for submitting PipelineJobs to Vertex AI, and a Cloud Scheduler job for submitting PipelineJobs on a recurring basis. These automatic integrations empower data scientists to take their experiments to production more quickly, allowing them to focus on what they do best: providing actionable insights through data.\n'
            '\n'
            '# User Guide\n'
            '\n'
            'For a user-guide, please view these [slides](https://github.com/GoogleCloudPlatform/automlops/blob/main/AutoMLOps_Implementation_Guide_External.pdf).\n'
            '\n'
            '# Layout\n'
            '\n'
            '```bash\n'
            '.\n'
            f'{cloud_run_dirs}'
            '├── components                                     : Custom vertex pipeline components.\n'
            '    ├──component_base                              : Contains all the python files, Dockerfile and requirements.txt\n'
            '    ├──component_a                                 : Components generated using AutoMLOps\n'
            '    ├──...\n'
            '├── images                                         : Custom container images for training models.\n'
            '├── pipelines                                      : Vertex ai pipeline definitions.\n'
            '    ├── pipeline.py                                : Full pipeline definition.\n'
            '    ├── pipeline_runner.py                         : Sends a PipelineJob to Vertex AI.\n'
            '    ├── runtime_parameters                         : Variables to be used in a PipelineJob.\n'
            '        ├── pipeline_parameter_values.json         : Json containing pipeline parameters.\n'  
            '├── configs                                        : Configurations for defining vertex ai pipeline.\n'
            '    ├── defaults.yaml                              : PipelineJob configuration variables.\n'
            '├── scripts                                        : Scripts for manually triggering the cloud run service.\n'
            '    ├── build_components.sh                        : Submits a Cloud Build job that builds and deploys the components.\n'
            '    ├── build_pipeline_spec.sh                     : Builds the pipeline specs.\n'
            '    ├── create_resources.sh                        : Creates an artifact registry and gs bucket if they do not already exist.\n'
            '    ├── run_pipeline.sh                            : Submit the PipelineJob to Vertex AI.\n'
            '    ├── run_all.sh                                 : Builds components, pipeline specs, and submits the PipelineJob.\n'
            '└── cloudbuild.yaml                                : Cloudbuild configuration file for building custom components.\n'
            '```\n')
