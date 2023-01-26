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
       cb_trigger_location: str = 'us-central1',
       cb_trigger_name: str = 'automlops-trigger',
       cloud_run_location: str = 'us-central1',
       cloud_run_name: str = 'run-pipeline',
       csr_branch_name: str = 'automlops',
       csr_name: str = 'AutoMLOps-repo',
       gs_bucket_location: str = 'us-central1',
       gs_bucket_name: str = None,
       parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json',
       pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json',
       pipeline_runner_sa: str = None,
       run_local: bool = True,
       schedule_location: str = 'us-central1',
       schedule_name: str = 'AutoMLOps-schedule',
       schedule_pattern: str = 'No Schedule Specified',
       use_kfp_spec: bool = False):
    """Generates relevant pipeline and component artifacts,
       then builds, compiles, and submits the PipelineJob.

    Args:
        project_id: The project ID.
        pipeline_params: Dictionary containing runtime pipeline parameters.
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        cb_trigger_location: The location of the cloudbuild trigger.
        cb_trigger_name: The name of the cloudbuild trigger.
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        csr_branch_name: The name of the csr branch to push to to trigger cb job.
        csr_name: The name of the cloud source repo to use.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        parameter_values_path: Path to json pipeline params.
        pipeline_job_spec_path: Path to the compiled pipeline job spec.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        use_kfp_spec: Flag that determines the format of the component yamls.
    """
    generate(project_id, pipeline_params, af_registry_location,
             af_registry_name, cb_trigger_location, cb_trigger_name,
             cloud_run_location, cloud_run_name, csr_branch_name,
             csr_name, gs_bucket_location, gs_bucket_name,
             parameter_values_path, pipeline_job_spec_path, pipeline_runner_sa,
             run_local, schedule_location, schedule_name,
             schedule_pattern, use_kfp_spec)
    run(run_local)

def generate(project_id: str,
             pipeline_params: dict,
             af_registry_location: str = 'us-central1',
             af_registry_name: str = 'vertex-mlops-af',
             cb_trigger_location: str = 'us-central1',
             cb_trigger_name: str = 'automlops-trigger',
             cloud_run_location: str = 'us-central1',
             cloud_run_name: str = 'run-pipeline',
             csr_branch_name: str = 'automlops',
             csr_name: str = 'AutoMLOps-repo',
             gs_bucket_location: str = 'us-central1',
             gs_bucket_name: str = None,
             parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json',
             pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json',
             pipeline_runner_sa: str = None,
             run_local: bool = True,
             schedule_location: str = 'us-central1',
             schedule_name: str = 'AutoMLOps-schedule',
             schedule_pattern: str = 'No Schedule Specified',
             use_kfp_spec: bool = False):
    """Generates relevant pipeline and component artifacts.

    Args: See go() function.
    """
    BuilderUtils.validate_schedule(schedule_pattern, run_local)
    default_bucket_name = f'{project_id}-bucket' if gs_bucket_name is None else gs_bucket_name
    default_pipeline_runner_sa = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com' if pipeline_runner_sa is None else pipeline_runner_sa
    BuilderUtils.make_dirs(DIRS)
    create_default_config(af_registry_location, af_registry_name, cb_trigger_location,
                          cb_trigger_name, cloud_run_location, cloud_run_name,
                          csr_branch_name, csr_name, gs_bucket_location,
                          default_bucket_name, parameter_values_path, pipeline_job_spec_path,
                          default_pipeline_runner_sa, project_id, schedule_location,
                          schedule_name, schedule_pattern)

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
    cb_trigger_location = defaults['gcp']['cb_trigger_location']
    csr_name = defaults['gcp']['cloud_source_repository']
    BuilderUtils.execute_process('./'+RESOURCES_SH_FILE, to_null=False)

    if run_local:
        os.chdir(TOP_LVL_NAME)
        BuilderUtils.execute_process('./scripts/run_all.sh', to_null=False)
        os.chdir('../')
    else:
        try:
            push_to_csr()
            print('Waiting for cloudbuild job to complete...', end='')
            cmd = f'''gcloud builds list --region={cb_trigger_location} | grep {csr_name} | grep WORKING || true'''
            while subprocess.check_output([cmd], shell=True, stderr=subprocess.STDOUT):
                print('..', end='', flush=True)
                time.sleep(30)
            time.sleep(5)

            print('Submitting PipelineJob...')
            os.chdir(TOP_LVL_NAME)
            BuilderUtils.execute_process('./scripts/submit_to_runner_svc.sh', to_null=False)

            if defaults['gcp']['cloud_schedule_pattern'] != 'No Schedule Specified':
                print('Creating Cloud Scheduler Job')
                BuilderUtils.execute_process('./scripts/create_scheduler.sh', to_null=False)

            os.chdir('../')
        except Exception as err:
            raise Exception(f'Error pushing to repo. {err}') from err
    resources_generation_manifest(defaults, run_local)

def resources_generation_manifest(defaults: dict, run_local: bool):
    """Prints urls of generated resources.

    Args:
        defaults: Dictionary containing resource names.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    print('\n'
          '#################################################################\n'
          '#                                                               #\n'
          '#                       RESOURCES MANIFEST                      #\n'
          '#---------------------------------------------------------------#\n'
          '#     Generated resources can be found at the following urls    #\n'
          '#                                                               #\n'
          '#################################################################\n')
    print(f'''Google Cloud Storage Bucket: https://console.cloud.google.com/storage/{defaults['gcp']['gs_bucket_name']}''')
    print(f'''Artifact Registry: https://console.cloud.google.com/artifacts/docker/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_location']}/{defaults['gcp']['af_registry_name']}''')
    print(f'''Service Accounts: https://console.cloud.google.com/iam-admin/serviceaccounts?project={defaults['gcp']['project_id']}''')
    print('APIs: https://console.cloud.google.com/apis')
    print(f'''Cloud Source Repository: https://source.cloud.google.com/{defaults['gcp']['project_id']}/{defaults['gcp']['cloud_source_repository']}/+/{defaults['gcp']['cloud_source_repository_branch']}:''')
    print(f'''Cloud Build Jobs: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['cb_trigger_location']}''')
    print('Vertex AI Pipeline Runs: https://console.cloud.google.com/vertex-ai/pipelines/runs')
    if not run_local:
        print(f'''Cloud Build Trigger: https://console.cloud.google.com/cloud-build/triggers;region={defaults['gcp']['cb_trigger_location']}''')
        print(f'''Cloud Run Service: https://console.cloud.google.com/run/detail/{defaults['gcp']['cloud_run_location']}/{defaults['gcp']['cloud_run_name']}''')
    if defaults['gcp']['cloud_schedule_pattern'] != 'No Schedule Specified':
        print('Cloud Scheduler Job: https://console.cloud.google.com/cloudscheduler')

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

def push_to_csr():
    """Initializes a git repo if one doesn't already exist,
       then pushes to the specified branch and triggers the cloudbuild job.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
    if not os.path.exists('.git'):
        BuilderUtils.execute_process('git init', to_null=False)
        BuilderUtils.execute_process('''git config --global credential.'https://source.developers.google.com'.helper gcloud.sh''', to_null=False)
        BuilderUtils.execute_process(f'''git remote add origin https://source.developers.google.com/p/{defaults['gcp']['project_id']}/r/{defaults['gcp']['cloud_source_repository']}''', to_null=False)
        BuilderUtils.execute_process(f'''git checkout -B {defaults['gcp']['cloud_source_repository_branch']}''', to_null=False)
        # This will initialize the branch, a second push will be required to trigger the cloudbuild job after initializing
        BuilderUtils.execute_process(f'git add {TOP_LVL_NAME}', to_null=False)
        BuilderUtils.execute_process('''git commit -m 'init' ''', to_null=False)
        BuilderUtils.execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)

    BuilderUtils.execute_process(f'touch {TOP_LVL_NAME}scripts/pipeline_spec/.gitkeep', to_null=False) # needed to keep dir here
    BuilderUtils.execute_process('git add .', to_null=False)
    BuilderUtils.execute_process('''git commit -m 'Run AutoMLOps' ''', to_null=False)
    BuilderUtils.execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)
    print(f'''Pushing code to {defaults['gcp']['cloud_source_repository_branch']} branch, triggering cloudbuild...''')
    time.sleep(30)

def create_default_config(af_registry_location: str,
                          af_registry_name: str,
                          cb_trigger_location: str,
                          cb_trigger_name: str,
                          cloud_run_location: str,
                          cloud_run_name: str,
                          csr_branch_name: str,
                          csr_name: str,
                          gs_bucket_location: str,
                          gs_bucket_name: str,
                          parameter_values_path: str,
                          pipeline_job_spec_path: str,
                          pipeline_runner_sa: str,
                          project_id: str,
                          schedule_location: str,
                          schedule_name: str,
                          schedule_pattern: str):
    """Writes default variables to defaults.yaml. This defaults
       file is used by subsequent functions and by the pipeline
       files themselves.

    Args:
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        cb_trigger_location: The location of the cloudbuild trigger.
        cb_trigger_name: The name of the cloudbuild trigger.
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        csr_branch_name: The name of the csr branch to push to to trigger cb job.
        csr_name: The name of the cloud source repo to use.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        parameter_values_path: Path to json pipeline params.
        pipeline_job_spec_path: Path to the compiled pipeline job spec.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        project_id: The project ID.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
    """
    defaults = (BuilderUtils.LICENSE +
        f'gcp:\n'
        f'  af_registry_location: {af_registry_location}\n'
        f'  af_registry_name: {af_registry_name}\n'
        f'  cb_trigger_location: {cb_trigger_location}\n'
        f'  cb_trigger_name: {cb_trigger_name}\n'
        f'  cloud_run_location: {cloud_run_location}\n'
        f'  cloud_run_name: {cloud_run_name}\n'
        f'  cloud_schedule_location: {schedule_location}\n'
        f'  cloud_schedule_name: {schedule_name}\n'
        f'  cloud_schedule_pattern: {schedule_pattern}\n'
        f'  cloud_source_repository: {csr_name}\n'
        f'  cloud_source_repository_branch: {csr_branch_name}\n'
        f'  gs_bucket_name: {gs_bucket_name}\n'
        f'  pipeline_runner_service_account: {pipeline_runner_sa}\n'
        f'  project_id: {project_id}\n'
        f'\n'
        f'pipelines:\n'
        f'  parameter_values_path: {parameter_values_path}\n'
        f'  pipeline_component_directory: components\n'
        f'  pipeline_job_spec_path: {pipeline_job_spec_path}\n'
        f'  pipeline_region: {gs_bucket_location}\n'
        f'  pipeline_storage_path: gs://{gs_bucket_name}/pipeline_root\n')
    BuilderUtils.write_file(DEFAULTS_FILE, defaults, 'w+')

def create_scripts(run_local: bool):
    """Writes various shell scripts used for pipeline and component
       construction, as well as pipeline execution.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
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
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        f'# Calls the Cloud Run pipeline Runner service to submit\n'
        f'# a PipelineJob to Vertex AI. This script should run from\n'
        f'# the main directory. Change directory in case this is not the script root.\n'
        f'\n'
        f'''GREEN='\033[0;32m'\n'''
        f'''NC='\033[0m'\n'''
        f'''RUNNER_SA={defaults['gcp']['pipeline_runner_service_account']}\n'''
        f'''PIPELINE_RUNNER_SVC_URL=`gcloud run services describe {defaults['gcp']['cloud_run_name']} --platform managed --region {defaults['gcp']['cloud_run_location']} --format 'value(status.url)'`\n'''
        f'ID_TOKEN=`gcloud auth print-identity-token --impersonate-service-account=$RUNNER_SA --audiences="$PIPELINE_RUNNER_SVC_URL" --quiet`\n'
        f'echo -e "$GREEN Submitting training job to Cloud Runner Service $PIPELINE_RUNNER_SVC_URL using @pipelines/runtime_parameters/pipeline_parameter_values.json $NC"\n'
        f'curl -v --ipv4 --http1.1 --trace-ascii - $PIPELINE_RUNNER_SVC_URL \{newline}'
        f'  -X POST \{newline}'
        f'  -H "Authorization:bearer $ID_TOKEN" \{newline}'
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
        '#!/bin/bash\n' + BuilderUtils.LICENSE +
        f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
        f'\n'
        f'''GREEN='\033[0;32m'\n'''
        f'''NC='\033[0m'\n'''
        f'''AF_REGISTRY_NAME={defaults['gcp']['af_registry_name']}\n'''
        f'''AF_REGISTRY_LOCATION={defaults['gcp']['af_registry_location']}\n'''
        f'''PROJECT_ID={defaults['gcp']['project_id']}\n'''
        f'''PROJECT_NUMBER=`gcloud projects describe {defaults['gcp']['project_id']} --format 'value(projectNumber)'`\n'''
        f'''BUCKET_NAME={defaults['gcp']['gs_bucket_name']}\n'''
        f'''BUCKET_LOCATION={defaults['pipelines']['pipeline_region']}\n'''
        f'''SERVICE_ACCOUNT_NAME={defaults['gcp']['pipeline_runner_service_account'].split('@')[0]}\n'''
        f'''SERVICE_ACCOUNT_FULL={defaults['gcp']['pipeline_runner_service_account']}\n'''
        f'''CLOUD_SOURCE_REPO={defaults['gcp']['cloud_source_repository']}\n'''
        f'''CLOUD_SOURCE_REPO_BRANCH={defaults['gcp']['cloud_source_repository_branch']}\n'''
        f'''CB_TRIGGER_LOCATION={defaults['gcp']['cb_trigger_location']}\n'''
        f'''CB_TRIGGER_NAME={defaults['gcp']['cb_trigger_name']}\n'''
        f'''EXECUTING_ACCOUNT=`gcloud config list account --format "value(core.account)"`\n'''
        f'\n'
        f'if ! (gcloud config list account --format "value(core.account)" | grep --fixed-strings "gserviceaccount"); then\n'
        f'\n'
        f'  EXECUTING_ACCOUNT_TYPE=user\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  EXECUTING_ACCOUNT_TYPE=serviceAccount\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'echo -e "$GREEN Updating required API services in project $PROJECT_ID $NC"\n'
        f'gcloud services enable cloudresourcemanager.googleapis.com \{newline}'
        f'  aiplatform.googleapis.com \{newline}'
        f'  artifactregistry.googleapis.com \{newline}'
        f'  cloudbuild.googleapis.com \{newline}'
        f'  cloudscheduler.googleapis.com \{newline}'
        f'  compute.googleapis.com \{newline}'
        f'  iam.googleapis.com \{newline}'
        f'  iamcredentials.googleapis.com \{newline}'
        f'  ml.googleapis.com \{newline}'
        f'  run.googleapis.com \{newline}'
        f'  storage.googleapis.com \{newline}'
        f'  sourcerepo.googleapis.com\n'
        f'\n'
        f'echo -e "$GREEN Checking for Artifact Registry: $AF_REGISTRY_NAME in project $PROJECT_ID $NC"\n'
        f'if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "$AF_REGISTRY_NAME"); then\n'
        f'\n'
        f'  echo "Creating Artifact Registry: ${left_bracket}AF_REGISTRY_NAME{right_bracket} in project $PROJECT_ID"\n'
        f'  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \{newline}'
        f'    --repository-format=docker \{newline}'
        f'    --location=$AF_REGISTRY_LOCATION \{newline}'
        f'    --project="$PROJECT_ID" \{newline}'
        f'    --description="Artifact Registry ${left_bracket}AF_REGISTRY_NAME{right_bracket} in ${left_bracket}AF_REGISTRY_LOCATION{right_bracket}." \n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "Artifact Registry: ${left_bracket}AF_REGISTRY_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'\n'
        f'echo -e "$GREEN Checking for GS Bucket: $BUCKET_NAME in project $PROJECT_ID $NC"\n'
        f'if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then\n'
        f'\n'
        f'  echo "Creating GS Bucket: ${left_bracket}BUCKET_NAME{right_bracket} in project $PROJECT_ID"\n'
        f'  gsutil mb -l ${left_bracket}BUCKET_LOCATION{right_bracket} gs://$BUCKET_NAME\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "GS Bucket: ${left_bracket}BUCKET_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'echo -e "$GREEN Checking for Service Account: $SERVICE_ACCOUNT_NAME in project $PROJECT_ID $NC"\n'
        f'if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep --fixed-strings "$SERVICE_ACCOUNT_FULL"); then\n'
        f'\n'
        f'  echo "Creating Service Account: ${left_bracket}SERVICE_ACCOUNT_NAME{right_bracket} in project $PROJECT_ID"\n'
        f'  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \{newline}'
        f'      --description="For submitting PipelineJobs" \{newline}'
        f'      --display-name="Pipeline Runner Service Account"\n'
        f'else\n'
        f'\n'
        f'  echo "Service Account: ${left_bracket}SERVICE_ACCOUNT_NAME{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n'
        f'\n'
        f'echo -e "$GREEN Updating required IAM roles in project $PROJECT_ID $NC"\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/aiplatform.user" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/artifactregistry.reader" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/bigquery.user" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'   --role="roles/bigquery.dataEditor" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/iam.serviceAccountUser" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/storage.admin" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{newline}'
        f'    --role="roles/run.admin" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{newline}'
        f'    --role="roles/run.admin" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{newline}'
        f'    --role="roles/iam.serviceAccountUser" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_FULL \{newline}'
        f'    --member="$EXECUTING_ACCOUNT_TYPE:$EXECUTING_ACCOUNT" \{newline}'
        f'    --role="roles/iam.serviceAccountTokenCreator" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'gcloud projects add-iam-policy-binding $PROJECT_ID \{newline}'
        f'    --member="$EXECUTING_ACCOUNT_TYPE:$EXECUTING_ACCOUNT" \{newline}'
        f'    --role="roles/iam.serviceAccountUser" \{newline}'
        f'    --no-user-output-enabled\n'
        f'\n'
        f'echo -e "$GREEN Checking for Cloud Source Repository: $CLOUD_SOURCE_REPO in project $PROJECT_ID $NC"\n'
        f'if ! (gcloud source repos list --project="$PROJECT_ID" | grep --fixed-strings "$CLOUD_SOURCE_REPO"); then\n'
        f'\n'
        f'  echo "Creating Cloud Source Repository: ${left_bracket}CLOUD_SOURCE_REPO{right_bracket} in project $PROJECT_ID"\n'
        f'  gcloud source repos create $CLOUD_SOURCE_REPO\n'
        f'\n'
        f'else\n'
        f'\n'
        f'  echo "Cloud Source Repository: ${left_bracket}CLOUD_SOURCE_REPO{right_bracket} already exists in project $PROJECT_ID"\n'
        f'\n'
        f'fi\n')
    if not run_local:
        create_resources_script += (
            f'\n'
            f'# Create cloud build trigger\n'
            f'echo -e "$GREEN Checking for Cloudbuild Trigger: $CB_TRIGGER_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud beta builds triggers list --project="$PROJECT_ID" --region="$CB_TRIGGER_LOCATION" | grep --fixed-strings "name: $CB_TRIGGER_NAME"); then\n'
            f'\n'
            f'  echo "Creating Cloudbuild Trigger on branch $CLOUD_SOURCE_REPO_BRANCH in project $PROJECT_ID for repo ${left_bracket}CLOUD_SOURCE_REPO{right_bracket}"\n'
            f'  gcloud beta builds triggers create cloud-source-repositories \{newline}'
            f'  --region=$CB_TRIGGER_LOCATION \{newline}'
            f'  --name=$CB_TRIGGER_NAME \{newline}'
            f'  --repo=$CLOUD_SOURCE_REPO \{newline}'
            f'  --branch-pattern="$CLOUD_SOURCE_REPO_BRANCH" \{newline}'
            f'  --build-config={TOP_LVL_NAME}cloudbuild.yaml\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${left_bracket}CLOUD_SOURCE_REPO{right_bracket}"\n'
            f'\n'
            f'fi\n')
    BuilderUtils.write_and_chmod(RESOURCES_SH_FILE, create_resources_script)
    if defaults['gcp']['cloud_schedule_pattern'] != 'No Schedule Specified':
        create_schedule_script = (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            f'# Creates a pipeline schedule.\n'
            f'# This script should run from the {TOP_LVL_NAME} directory\n'
            f'# Change directory in case this is not the script root.\n'
            f'\n'
            f'''GREEN='\033[0;32m'\n'''
            f'''NC='\033[0m'\n'''
            f'''PROJECT_ID={defaults['gcp']['project_id']}\n'''
            f'''PARAMS_PATH={defaults['pipelines']['parameter_values_path']}\n'''
            f'''SERVICE_ACCOUNT_FULL={defaults['gcp']['pipeline_runner_service_account']}\n'''
            f'''CLOUD_SOURCE_REPO={defaults['gcp']['cloud_source_repository']}\n'''
            f'''PIPELINE_RUNNER_SVC_URL=`gcloud run services describe {defaults['gcp']['cloud_run_name']} --platform managed --region {defaults['gcp']['cloud_run_location']} --format 'value(status.url)'`\n'''
            f'''CLOUD_SCHEDULE_LOCATION={defaults['gcp']['cloud_schedule_location']}\n'''
            f'''CLOUD_SCHEDULE_NAME={defaults['gcp']['cloud_schedule_name']}\n'''
            f'''CLOUD_SCHEDULE_PATTERN="{defaults['gcp']['cloud_schedule_pattern']}"\n'''
            f'\n'
            f'echo -e "$GREEN Checking for Cloud Scheduler Job: $CLOUD_SCHEDULE_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud scheduler jobs list --project="$PROJECT_ID" --location="$CLOUD_SCHEDULE_LOCATION" | grep --fixed-strings "$CLOUD_SCHEDULE_NAME") && [ -n "$PIPELINE_RUNNER_SVC_URL" ]; then\n'
            f'\n'
            f'  echo "Creating Cloud Scheduler Job: $CLOUD_SCHEDULE_NAME in project $PROJECT_ID"\n'
            f'  gcloud scheduler jobs create http $CLOUD_SCHEDULE_NAME \{newline}'
            f'  --schedule="$CLOUD_SCHEDULE_PATTERN" \{newline}'
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
        f'''           "{defaults['gcp']['cloud_run_name']}",\n'''
        f'''           "--image",\n'''
        f'''           "{defaults['gcp']['af_registry_location']}-docker.pkg.dev/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_name']}/run_pipeline:latest",\n'''
        f'''           "--region",\n'''
        f'''           "{defaults['gcp']['cloud_run_location']}",\n'''
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
