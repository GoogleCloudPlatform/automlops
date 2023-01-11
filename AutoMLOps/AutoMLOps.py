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

"""AutoMLOps is a tool that generates a production-style MLOps pipeline
   from Jupyter Notebooks."""

import os
import re
import time
import subprocess

# need to update this sys pathing
from . import BuilderUtils
from . import ComponentBuilder
from . import PipelineBuilder
from . import CloudRunBuilder
from . import JupyterUtilsMagic

TOP_LVL_NAME = 'AutoMLOps/'
DEFAULTS_FILE = TOP_LVL_NAME + 'configs/defaults.yaml'
PIPELINE_SPEC_SH_FILE = TOP_LVL_NAME + 'scripts/build_pipeline_spec.sh'
BUILD_COMPONENTS_SH_FILE = TOP_LVL_NAME + 'scripts/build_components.sh'
RUN_PIPELINE_SH_FILE = TOP_LVL_NAME + 'scripts/run_pipeline.sh'
RUN_ALL_SH_FILE = TOP_LVL_NAME + 'scripts/run_all.sh'
RESOURCES_SH_FILE = TOP_LVL_NAME + 'scripts/create_resources.sh'
SCHEDULER_SH_FILE = TOP_LVL_NAME + 'scripts/create_scheduler.sh'
SUBMIT_JOB_FILE = TOP_LVL_NAME + 'scripts/submit_to_runner_svc.sh'
CLOUDBUILD_FILE = TOP_LVL_NAME + 'cloudbuild.yaml'
PIPELINE_FILE = TOP_LVL_NAME + 'pipelines/pipeline.py'
IMPORTS_FILE = '.imports.py'
DEFAULT_IMAGE = 'python:3.9'
COMPONENT_BASE = TOP_LVL_NAME + 'components/component_base'
COMPONENT_BASE_SRC = TOP_LVL_NAME + 'components/component_base/src'
OUTPUT_DIR = BuilderUtils.TMPFILES_DIR
DIRS = [
    TOP_LVL_NAME,
    TOP_LVL_NAME + 'components',
    TOP_LVL_NAME + 'components/component_base',
    TOP_LVL_NAME + 'components/component_base/src',
    TOP_LVL_NAME + 'configs',
    TOP_LVL_NAME + 'images',
    TOP_LVL_NAME + 'pipelines',
    TOP_LVL_NAME + 'pipelines/runtime_parameters',
    TOP_LVL_NAME + 'scripts',
    TOP_LVL_NAME + 'scripts/pipeline_spec']

# pylint: disable=line-too-long
def go(project_id: str,
       pipeline_params: dict,
       af_registry_location: str = 'us-central1',
       af_registry_name: str = 'vertex-mlops-af',
       gs_bucket_location: str = 'us-central1',
       gs_bucket_name: str = None,
       csr_name: str = 'AutoMLOps-repo',
       schedule: str = 'No Schedule Specified',
       schedule_location: str = 'us-central1',
       parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json',
       pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json',
       pipeline_runner_sa: str = None,
       use_kfp_spec: bool = False,
       run_local: bool = True):
    """Generates relevant pipeline and component artifacts,
       then builds, compiles, and submits the PipelineJob.

    Args:
        project_id: The project ID.
        pipeline_params: Dictionary containing runtime pipeline parameters.
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        csr_name: The name of the cloud source repo to use.
        schedule: Cron formatted value used to create a Scheduled retrain job.
        schedule_location: The location of the scheduler resource.
        parameter_values_path: Path to json pipeline params.
        pipeline_job_spec_path: Path to the compiled pipeline job spec.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        use_kfp_spec: Flag that determines the format of the component yamls.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    generate(project_id, pipeline_params, af_registry_location,
             af_registry_name, gs_bucket_location, gs_bucket_name,
             csr_name, schedule, schedule_location,
             parameter_values_path, pipeline_job_spec_path,
             pipeline_runner_sa, use_kfp_spec, run_local)
    run(run_local)

def generate(project_id: str,
             pipeline_params: dict,
             af_registry_location: str = 'us-central1',
             af_registry_name: str = 'vertex-mlops-af',
             gs_bucket_location: str = 'us-central1',
             gs_bucket_name: str = None,
             csr_name: str = 'AutoMLOps-repo',
             schedule: str = 'No Schedule Specified',
             schedule_location: str = 'us-central1',
             parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json',
             pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json',
             pipeline_runner_sa: str = None,
             use_kfp_spec: bool = False,
             run_local: bool = True):
    """Generates relevant pipeline and component artifacts.

    Args: See go() function.
    """
    BuilderUtils.validate_schedule(schedule, run_local)
    default_bucket_name = f'{project_id}-bucket' if gs_bucket_name is None else gs_bucket_name
    default_pipeline_runner_sa = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com' if pipeline_runner_sa is None else pipeline_runner_sa
    BuilderUtils.make_dirs(DIRS)
    create_default_config(project_id, af_registry_location, af_registry_name,
                          gs_bucket_location, default_bucket_name, csr_name,
                          schedule, schedule_location, parameter_values_path,
                          pipeline_job_spec_path, default_pipeline_runner_sa)
    create_scripts(run_local)
    create_cloudbuild_config(run_local)
    copy_pipeline()
    components_path_list = BuilderUtils.get_components_list()
    for path in components_path_list:
        ComponentBuilder.formalize(path, TOP_LVL_NAME, DEFAULTS_FILE, use_kfp_spec)
    PipelineBuilder.formalize(pipeline_params, parameter_values_path, TOP_LVL_NAME)
    if not use_kfp_spec:
        autoflake_srcfiles()
    create_requirements(use_kfp_spec)
    create_dockerfile()
    if not run_local:
        CloudRunBuilder.formalize(TOP_LVL_NAME)

def run(run_local: bool):
    """Builds, compiles, and submits the PipelineJob.

    TODO(@srastatter): clean this up, messy
    - chdir is bad practice, can cause issues when the scripts fail

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
    csr_name = defaults['gcp']['cloud_source_repository']
    BuilderUtils.execute_script(RESOURCES_SH_FILE, to_null=False)
    move_files(csr_name)

    if run_local:
        os.chdir(TOP_LVL_NAME)
        BuilderUtils.execute_script('scripts/run_all.sh', to_null=False)
        os.chdir('../')
    else:
        try:
            # Push the code to csr
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Run AutoMLOps'], check=True)
            subprocess.run(['git', 'push', '--all', 'origin', '--force'], check=True)
            print('Pushing code to main branch, triggering cloudbuild...')
            time.sleep(30)
            print('Waiting for cloudbuild job to complete...', end='')

            cmd = f'''gcloud builds list | grep {csr_name} | grep WORKING || true'''
            while (subprocess.check_output([cmd], shell=True, stderr=subprocess.STDOUT)):
                print('..', end='', flush=True)
                time.sleep(30)
            time.sleep(5)

            print('Submitting PipelineJob...')
            os.chdir(TOP_LVL_NAME)
            BuilderUtils.execute_script(f'./scripts/submit_to_runner_svc.sh', to_null=False)

            if defaults['gcp']['cloud_schedule'] != 'No Schedule Specified':
                print('Creating Cloud Scheduler Job')
                BuilderUtils.execute_script('scripts/create_scheduler.sh', to_null=False)

            os.chdir('../')
        except Exception as err:
            raise Exception(f'Error pushing to repo. {err}') from err


def copy_pipeline():
    """Copy the pipeline scaffold from the tmpfiles dir to the permanent
       pipelines directory. Requires that the make_dirs function has
       been called already.
    """
    try:
        subprocess.run(['cp', f'{BuilderUtils.PIPELINE_TMPFILE}', f'{PIPELINE_FILE}'], check=True)
    except FileNotFoundError as err:
        raise Exception(f'Pipeline file not found. '
                        f'Rerun pipeline cell. {err}') from err

def move_files(csr_name: str):
    """Move git repo over to AutoMLOps folder.

    Args:
        csr_name: The name of the cloud source repo to use.
    """
    try:
        subprocess.run(['mv', f'{csr_name}/.git', '.'], check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        pass # git repo already exists
    try:
        subprocess.run(['rm', '-rf', f'{csr_name}'], check=True)
    except subprocess.CalledProcessError as err:
        raise Exception(f'Error deleting file. {err}') from err
    try:
        subprocess.run(['touch', f'{TOP_LVL_NAME}scripts/pipeline_spec/.gitkeep'], check=True) # needed to keep dir here
    except subprocess.CalledProcessError as err:
        raise Exception(f'Error touching file. {err}') from err

def create_default_config(project_id: str,
                          af_registry_location: str,
                          af_registry_name: str,
                          gs_bucket_location: str,
                          gs_bucket_name: str,
                          csr_name: str,
                          schedule: str,
                          schedule_location: str,
                          parameter_values_path: str,
                          pipeline_job_spec_path: str,
                          pipeline_runner_sa: str):
    """Writes default variables to defaults.yaml. This defaults
       file is used by subsequent functions and by the pipeline
       files themselves.

    Args:
        project_id: The project ID.
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        csr_name: The name of the cloud source repo to use.
        schedule: Cron formatted value used to create a Scheduled retrain job.
        schedule_location: The location of the scheduler resource.
        parameter_values_path: Path to json pipeline params.
        pipeline_job_spec_path: Path to the compiled pipeline job spec.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
    """
    defaults = (BuilderUtils.LICENSE +
        f'gcp:\n'
        f'  project_id: {project_id}\n'
        f'  af_registry_location: {af_registry_location}\n'
        f'  af_registry_name: {af_registry_name}\n'
        f'  gs_bucket_name: {gs_bucket_name}\n'
        f'  pipeline_runner_service_account: {pipeline_runner_sa}\n'
        f'  cloud_source_repository: {csr_name}\n'
        f'  cloud_schedule: {schedule}\n'
        f'  cloud_schedule_location: {schedule_location}\n'
        f'\n'
        f'pipelines:\n'
        f'  pipeline_region: {gs_bucket_location}\n'
        f'  parameter_values_path: {parameter_values_path}\n'
        f'  pipeline_storage_path: gs://{gs_bucket_name}/pipeline_root\n'
        f'  pipeline_component_directory: components\n'
        f'  pipeline_job_spec_path: {pipeline_job_spec_path}\n')
    BuilderUtils.write_file(DEFAULTS_FILE, defaults, 'w+')

def create_scripts(run_local: bool):
    """Writes various shell scripts used for pipeline and component
       construction, as well as pipeline execution.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    newline = '\n'
    build_pipeline_spec = (
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        '# Builds the pipeline specs\n'
        f'# This script should run from the {TOP_LVL_NAME} directory\n'
        '# Change directory in case this is not the script root.\n'
        '\n'
        'CONFIG_FILE=configs/defaults.yaml\n'
        '\n'
        'python3 -m pipelines.pipeline --config $CONFIG_FILE\n')
    build_components = (
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        '# Submits a Cloud Build job that builds and deploys the components\n'
        f'# This script should run from the {TOP_LVL_NAME} directory\n'
        '# Change directory in case this is not the script root.\n'
        '\n'
        'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n')
    run_pipeline = (
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        '# Submits the PipelineJob to Vertex AI\n'
        f'# This script should run from the {TOP_LVL_NAME} directory\n'
        '# Change directory in case this is not the script root.\n'
        '\n'
        'CONFIG_FILE=configs/defaults.yaml\n'
        '\n'
        'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE\n')
    run_all = (
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        '# Builds components, pipeline specs, and submits the PipelineJob.\n'
        f'# This script should run from the {TOP_LVL_NAME} directory\n'
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
    # pylint: disable=anomalous-backslash-in-string
    submit_job = (
        f'#!/bin/bash\n' + BuilderUtils.LICENSE +
        f'# Calls the Cloud Run pipeline Runner service to submit\n'
        f'# a PipelineJob to Vertex AI. This script should run from\n'
        f'# the main directory. Change directory in case this is not the script root.\n'
        f'\n'
        f'''PIPELINE_RUNNER_SVC_URL=`gcloud run services describe run-pipeline --platform managed --region us-central1 --format 'value(status.url)'`'''
        f'\n'
        f'curl -v --ipv4 --http1.1 --trace-ascii - $PIPELINE_RUNNER_SVC_URL \{newline}'
        f'  -X POST \{newline}'
        f'  -H "Authorization:bearer $(gcloud auth print-identity-token --quiet)" \{newline}'
        f'  -H "Content-Type: application/json" \{newline}'
        f'  --data @pipelines/runtime_parameters/pipeline_parameter_values.json\n')
    BuilderUtils.write_and_chmod(PIPELINE_SPEC_SH_FILE, build_pipeline_spec)
    BuilderUtils.write_and_chmod(BUILD_COMPONENTS_SH_FILE, build_components)
    BuilderUtils.write_and_chmod(RUN_PIPELINE_SH_FILE, run_pipeline)
    BuilderUtils.write_and_chmod(RUN_ALL_SH_FILE, run_all)
    if not run_local:
        BuilderUtils.write_and_chmod(SUBMIT_JOB_FILE, submit_job)
    create_resources_scripts(run_local)

def create_resources_scripts(run_local: bool):
    """Writes create_resources.sh and create_scheduler.sh, which creates a specified
       artifact registry and gs bucket if they do not already exist. Also creates
       a service account to run Vertex AI Pipelines. Requires a defaults.yaml
       config to pull config vars from.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
    left_bracket = '{'
    right_bracket = '}'
    newline = '\n'
    # pylint: disable=anomalous-backslash-in-string
    create_resources_script = (
        f'#!/bin/bash\n' + BuilderUtils.LICENSE +
        f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
        f'\n'
        f'''AF_REGISTRY_NAME={defaults['gcp']['af_registry_name']}\n'''
        f'''AF_REGISTRY_LOCATION={defaults['gcp']['af_registry_location']}\n'''
        f'''PROJECT_ID={defaults['gcp']['project_id']}\n'''
        f'''PROJECT_NUMBER=`gcloud projects describe {defaults['gcp']['project_id']} --format 'value(projectNumber)'`\n'''
        f'''BUCKET_NAME={defaults['gcp']['gs_bucket_name']}\n'''
        f'''BUCKET_LOCATION={defaults['pipelines']['pipeline_region']}\n'''
        f'''SERVICE_ACCOUNT_NAME={defaults['gcp']['pipeline_runner_service_account'].split('@')[0]}\n'''
        f'''SERVICE_ACCOUNT_FULL={defaults['gcp']['pipeline_runner_service_account']}\n'''
        f'''CLOUD_SOURCE_REPO={defaults['gcp']['cloud_source_repository']}\n'''
        f'\n'
        f'# Enable APIs\n'
        f'gcloud services enable cloudresourcemanager.googleapis.com \{newline}'
        f'aiplatform.googleapis.com \{newline}'
        f'artifactregistry.googleapis.com \{newline}'
        f'cloudbuild.googleapis.com \{newline}'
        f'cloudscheduler.googleapis.com \{newline}'
        f'compute.googleapis.com \{newline}'
        f'iam.googleapis.com \{newline}'
        f'iamcredentials.googleapis.com \{newline}'
        f'ml.googleapis.com \{newline}'
        f'run.googleapis.com \{newline}'
        f'storage.googleapis.com \{newline}'
        f'sourcerepo.googleapis.com\n'
        f'\n'
        f'if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "$AF_REGISTRY_NAME"); then\n'
        f'\n'
        f'  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \{newline}'
        f'    --repository-format=docker \{newline}'
        f'    --location=$AF_REGISTRY_LOCATION \{newline}'
        f'    --project="$PROJECT_ID" \{newline}'
        f'    --description="Artifact Registry ${left_bracket}AF_REGISTRY_NAME{right_bracket} in ${left_bracket}AF_REGISTRY_LOCATION{right_bracket}." \n'
        f'else\n'
        f'\n'
        f'  echo "Artifact Registry: ${left_bracket}AF_REGISTRY_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'\n'
        f'if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then\n'
        f'\n'
        f'  gsutil mb -l ${left_bracket}BUCKET_LOCATION{right_bracket} gs://$BUCKET_NAME\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "GS Bucket: ${left_bracket}BUCKET_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep --fixed-strings "$SERVICE_ACCOUNT_FULL"); then\n'
        f'\n'
        f'  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \{newline}'
        f'      --description="For submitting PipelineJobs" \{newline}'
        f'      --display-name="Pipeline Runner Service Account"\n'
        f'else\n'
        f'\n'
        f'  echo "Service Account: ${left_bracket}SERVICE_ACCOUNT_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/aiplatform.user" \n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/artifactregistry.reader" \n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/bigquery.user" \n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'   --role="roles/bigquery.dataEditor" \n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/iam.serviceAccountUser" \n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/storage.admin"\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/run.admin"\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/iam.serviceAccountUser"\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{newline}'
        f'    --role="roles/run.admin"\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{newline}'
        f'    --role="roles/iam.serviceAccountUser"\n'
        f'\n'
        f'# Create source repo\n'
        f'if ! (gcloud source repos list --project="$PROJECT_ID" | grep --fixed-strings "$CLOUD_SOURCE_REPO"); then\n'
        f'\n'
        f'  gcloud source repos create $CLOUD_SOURCE_REPO\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "Cloud Source Repository: ${left_bracket}CLOUD_SOURCE_REPO{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'if ! (ls -a | grep $CLOUD_SOURCE_REPO); then\n'
        f'\n'
        f'  gcloud source repos clone $CLOUD_SOURCE_REPO --project=$PROJECT_ID\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "Directory path specified exists and is not empty"\n'
        f'\n'
        f'fi\n')
    if not run_local:
        create_resources_script += (
            f'\n'
            f'# Create cloud build trigger\n'
            f'# Account needs to have Cloud Build Editor\n'
            f'if ! (gcloud beta builds triggers list --project="$PROJECT_ID" | grep --fixed-strings "$CLOUD_SOURCE_REPO" && gcloud beta builds triggers list --project="$PROJECT_ID" | grep --fixed-strings "{TOP_LVL_NAME}cloudbuild.yaml"); then\n'
            f'\n'
            f'  gcloud beta builds triggers create cloud-source-repositories \{newline}'
            f'  --repo=$CLOUD_SOURCE_REPO \{newline}'
            f'  --branch-pattern="^(main|master)$" \{newline}'
            f'  --build-config={TOP_LVL_NAME}cloudbuild.yaml\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${left_bracket}CLOUD_SOURCE_REPO{right_bracket}"\n'
            f'\n'
            f'fi\n')
    BuilderUtils.write_and_chmod(RESOURCES_SH_FILE, create_resources_script)
    if defaults['gcp']['cloud_schedule'] != 'No Schedule Specified':
        create_schedule_script = (
            f'#!/bin/bash\n' + BuilderUtils.LICENSE +
            f'# Creates a pipeline schedule.\n'
            f'# This script should run from the {TOP_LVL_NAME} directory\n'
            f'# Change directory in case this is not the script root.\n'
            f'\n' # ADD GLOBALS
            f'''PROJECT_ID={defaults['gcp']['project_id']}\n'''
            f'''PARAMS_PATH={defaults['pipelines']['parameter_values_path']}\n'''
            f'''SERVICE_ACCOUNT_FULL={defaults['gcp']['pipeline_runner_service_account']}\n'''
            f'''CLOUD_SOURCE_REPO={defaults['gcp']['cloud_source_repository']}\n'''
            f'''PIPELINE_RUNNER_SVC_URL=`gcloud run services describe run-pipeline --platform managed --region us-central1 --format 'value(status.url)'`\n'''
            f'''CLOUD_SCHEDULE="{defaults['gcp']['cloud_schedule']}"\n'''
            f'''CLOUD_SCHEDULE_LOCATION={defaults['gcp']['cloud_schedule_location']}\n'''
            f'\n'
            f'# Create cloud scheduler\n'
            f'if ! (gcloud scheduler jobs list --project="$PROJECT_ID" --location="$CLOUD_SCHEDULE_LOCATION" | grep --fixed-strings "AutoMLOps-schedule") && [ -n "$PIPELINE_RUNNER_SVC_URL" ]; then\n'
            f'\n'
            f'  gcloud scheduler jobs create http AutoMLOps-schedule \{newline}'
            f'  --schedule="$CLOUD_SCHEDULE" \{newline}'
            f'  --uri=$PIPELINE_RUNNER_SVC_URL \{newline}'
            f'  --http-method=POST \{newline}'
            f'  --location=$CLOUD_SCHEDULE_LOCATION \{newline}'
            f'  --description="AutoMLOps cloud scheduled run." \{newline}'
            f'  --message-body-from-file=$PARAMS_PATH \{newline}'
            f'  --headers Content-Type=application/json,User-Agent=Google-Cloud-Scheduler \{newline}'
            f'  --oidc-service-account-email=$SERVICE_ACCOUNT_FULL\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloud Scheduler AutoMLOps resource already exists in project $PROJECT_ID or Cloud Runner service not found"\n'
            f'\n'
            f'fi\n')
        BuilderUtils.write_and_chmod(SCHEDULER_SH_FILE, create_schedule_script)

def create_cloudbuild_config(run_local: bool):
    """Writes a cloudbuild.yaml to the base directory.
       Requires a defaults.yaml config to pull config vars from.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
    cloudbuild_comp_config = (BuilderUtils.LICENSE +
        f'steps:\n'
        f'# ==============================================================================\n'
        f'# BUILD & PUSH CUSTOM COMPONENT IMAGES\n'
        f'# ==============================================================================\n'
        f'\n'
        f'''  # build the ccomponent_base image\n'''
        f'''  - name: "gcr.io/cloud-builders/docker"\n'''
        f'''    args: [ "build", "-t", "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/components/component_base:latest", "." ]\n'''
        f'''    dir: "{TOP_LVL_NAME}components/component_base"\n'''
        f'''    id: "build_component_base"\n'''
        f'''    waitFor: ["-"]\n'''
        f'\n'
        f'''  # push the component_base image\n'''
        f'''  - name: "gcr.io/cloud-builders/docker"\n'''
        f'''    args: ["push", "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/components/component_base:latest"]\n'''
        f'''    dir: "{TOP_LVL_NAME}components/component_base"\n'''
        f'''    id: "push_component_base"\n'''
        f'''    waitFor: ["build_component_base"]\n''')
    cloudbuild_cloudrun_config = (
        f'\n'
        f'# ==============================================================================\n'
        f'# BUILD & PUSH CLOUD RUN IMAGES\n'
        f'# ==============================================================================\n'
        f'\n'
        f'''  # build the run_pipeline image\n'''
        f'''  - name: 'gcr.io/cloud-builders/docker'\n'''
        f'''    args: [ "build", "-t", "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/run_pipeline:latest", "-f", "cloud_run/run_pipeline/Dockerfile", "." ]\n'''
        f'''    dir: "{TOP_LVL_NAME}"\n'''
        f'''    id: "build_run_pipeline"\n'''
        f'''    waitFor: ['push_component_base']\n'''
        f'\n'
        f'''  # push the run_pipeline image\n'''
        f'''  - name: "gcr.io/cloud-builders/docker"\n'''
        f'''    args: ["push", "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/run_pipeline:latest"]\n'''
        f'''    dir: "{TOP_LVL_NAME}"\n'''
        f'''    id: "push_run_pipeline"\n'''
        f'''    waitFor: ["build_run_pipeline"]\n'''
        f'\n'
        f'''  # deploy the cloud run service\n'''
        f'''  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"\n'''
        f'''    entrypoint: gcloud\n'''
        f'''    args: ["run",\n'''
        f'''           "deploy",\n'''
        f'''           "run-pipeline",\n'''
        f'''           "--image",\n'''
        f'''           "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/run_pipeline:latest",\n'''
        f'''           "--region",\n'''
        f'''           "us-central1",\n'''
        f'''           "--service-account",\n'''
        f'''           "{defaults['gcp']['pipeline_runner_service_account']}"]\n'''
        f'''    id: "deploy_run_pipeline"\n'''
        f'''    waitFor: ["push_run_pipeline"]\n''')
    custom_comp_image = (
        f'\n'
        f'images:\n'
        f'''  # custom component images\n'''
        f'''  - "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/components/component_base:latest"\n''')
    cloudrun_image = (
        f'''  # Cloud Run image\n'''
        f'''  - "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/run_pipeline:latest"\n''')
    if run_local:
        BuilderUtils.write_file(CLOUDBUILD_FILE, cloudbuild_comp_config + custom_comp_image, 'w+')
    else:
        BuilderUtils.write_file(CLOUDBUILD_FILE, cloudbuild_comp_config + cloudbuild_cloudrun_config
            + custom_comp_image + cloudrun_image, 'w+')

def autoflake_srcfiles():
    """Removes unused imports from the python srcfiles. By default,
       all imports listed in the imports cell will be written to
       each srcfile. Autoflake removes the ones not being used."""
    try:
        subprocess.run([f'python3 -m autoflake --in-place --remove-all-unused-imports {COMPONENT_BASE_SRC}/*.py'], shell=True, check=True)
    except Exception as err:
        raise Exception(f'Error executing autoflake. {err}') from err

def create_requirements(use_kfp_spec: bool):
    """Writes a requirements.txt to the component_base directory.
       If not using kfp spec, infers pip requirements from the
       python srcfiles using pipreqs. Some default gcp packages
       are included, as well as packages that are often missing
       in setup.py files (e.g db_types, pyarrow, gcsfs, fsspec).

    Args:
        use_kfp_spec: Flag that determines the format of the component yamls.
    """
    reqs_filename = f'{COMPONENT_BASE}/requirements.txt'
    if use_kfp_spec:
        BuilderUtils.delete_file(reqs_filename)
        components_path_list = BuilderUtils.get_components_list()
        for component_path in components_path_list:
            component_spec = BuilderUtils.read_yaml_file(component_path)
            reqs = component_spec['implementation']['container']['command'][2]
            formatted_reqs = re.findall('\'([^\']*)\'', reqs)
            reqs_str = ''.join(r+'\n' for r in formatted_reqs)
            BuilderUtils.write_file(reqs_filename, reqs_str, 'a+')
    else:
        gcp_reqs = (
            'google-cloud-aiplatform\n'
            'google-cloud-appengine-logging\n'
            'google-cloud-audit-log\n'
            'google-cloud-bigquery\n'
            'google-cloud-bigquery-storage\n'
            'google-cloud-bigtable\n'
            'google-cloud-core\n'
            'google-cloud-dataproc\n'
            'google-cloud-datastore\n'
            'google-cloud-dlp\n'
            'google-cloud-firestore\n'
            'google-cloud-kms\n'
            'google-cloud-language\n'
            'google-cloud-logging\n'
            'google-cloud-monitoring\n'
            'google-cloud-notebooks\n'
            'google-cloud-pipeline-components\n'
            'google-cloud-pubsub\n'
            'google-cloud-pubsublite\n'
            'google-cloud-recommendations-ai\n'
            'google-cloud-resource-manager\n'
            'google-cloud-scheduler\n'
            'google-cloud-spanner\n'
            'google-cloud-speech\n'
            'google-cloud-storage\n'
            'google-cloud-tasks\n'
            'google-cloud-translate\n'
            'google-cloud-videointelligence\n'
            'google-cloud-vision\n'
            'db_dtypes\n'
            'pyarrow\n'
            'gcsfs\n'
            'fsspec\n')
        try:
            subprocess.run([f'python3 -m pipreqs.pipreqs {COMPONENT_BASE} --mode no-pin --force'], shell=True, check=True,
                stdout=None,
                stderr=subprocess.STDOUT)
        except Exception as err:
            raise Exception(f'Error executing pipreqs. {err}') from err
        BuilderUtils.write_file(reqs_filename, gcp_reqs, 'a')

def create_dockerfile():
    """Writes a Dockerfile to the component_base directory."""
    # pylint: disable=anomalous-backslash-in-string
    dockerfile = (BuilderUtils.LICENSE +
        f'FROM {DEFAULT_IMAGE}\n'
        f'RUN python -m pip install --upgrade pip\n'
        f'COPY requirements.txt .\n'
        f'RUN python -m pip install -r \ \n'
        f'    requirements.txt --quiet --no-cache-dir \ \n'
        f'    && rm -f requirements.txt\n'
        f'COPY ./src /pipelines/component/src\n'
        f'ENTRYPOINT ["/bin/bash"]\n')
    BuilderUtils.write_file(f'{COMPONENT_BASE}/Dockerfile', dockerfile, 'w')

def makeComponent(name: str,
                  params: list,
                  description: str = None):
    """Wrapper function that creates a tmp component scaffold
       which will be used by the ComponentBuilder formalize function.

    Args:
        name: Component name.
        params: Component parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        description: Optional description of the component.
    """
    ComponentBuilder.create_component_scaffold(name,
        params, description)

def makePipeline(name: str,
                 params: list,
                 pipeline: list,
                 description: str = None):
    """Wrapper function that creates a tmp pipeline scaffold
       which will be used by the PipelineBuilder formalize function.

    Args:
        name: Pipeline name.
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        pipeline: Defines the components to use in the pipeline,
            their order, and a mapping of component params to
            pipeline params. A list of dictionaries, each dict
            specifies a custom component and contains keys:
                'component_name': name of the component
                'param_mapping': a list of tuples mapping ->
                    (component_param, pipeline_param)
        description: Optional description of the pipeline.
    """
    PipelineBuilder.create_pipeline_scaffold(name,
        params, pipeline, description)
