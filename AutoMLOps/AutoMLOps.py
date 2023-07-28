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

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import

import functools
import logging
import os
import sys
import subprocess
from typing import Callable, Dict, List, Optional

from AutoMLOps.utils.constants import (
    BASE_DIR,
    GENERATED_DEFAULTS_FILE,
    GENERATED_DIRS,
    GENERATED_RESOURCES_SH_FILE,
    OUTPUT_DIR
)
from AutoMLOps.utils.utils import (
    execute_process,
    make_dirs,
    read_yaml_file,
    validate_schedule,
)
from AutoMLOps.frameworks.kfp import builder as KfpBuilder
from AutoMLOps.frameworks.kfp import scaffold as KfpScaffold
from AutoMLOps.deployments.cloudbuild import builder as CloudBuildBuilder

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

make_dirs([OUTPUT_DIR])

def go(project_id: str,
       pipeline_params: Dict,
       af_registry_location: Optional[str] = 'us-central1',
       af_registry_name: Optional[str] = 'vertex-mlops-af',
       base_image: Optional[str] = 'python:3.9-slim',
       cb_trigger_location: Optional[str] = 'us-central1',
       cb_trigger_name: Optional[str] = 'automlops-trigger',
       cloud_run_location: Optional[str] = 'us-central1',
       cloud_run_name: Optional[str] = 'run-pipeline',
       cloud_tasks_queue_location: Optional[str] = 'us-central1',
       cloud_tasks_queue_name: Optional[str] = 'queueing-svc',
       csr_branch_name: Optional[str] = 'automlops',
       csr_name: Optional[str] = 'AutoMLOps-repo',
       custom_training_job_specs: Optional[List[Dict]] = None,
       gs_bucket_location: Optional[str] = 'us-central1',
       gs_bucket_name: Optional[str] = None,
       pipeline_runner_sa: Optional[str] = None,
       run_local: Optional[bool] = True,
       schedule_location: Optional[str] = 'us-central1',
       schedule_name: Optional[str] = 'AutoMLOps-schedule',
       schedule_pattern: Optional[str] = 'No Schedule Specified',
       vpc_connector: Optional[str] = 'No VPC Specified'):
    """Generates relevant pipeline and component artifacts,
       then builds, compiles, and submits the PipelineJob.

    Args:
        project_id: The project ID.
        pipeline_params: Dictionary containing runtime pipeline parameters.
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        base_image: The image to use in the component base dockerfile.
        cb_trigger_location: The location of the cloudbuild trigger.
        cb_trigger_name: The name of the cloudbuild trigger.
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        cloud_tasks_queue_location: The location of the cloud tasks queue.
        cloud_tasks_queue_name: The name of the cloud tasks queue.
        csr_branch_name: The name of the csr branch to push to to trigger cb job.
        csr_name: The name of the cloud source repo to use.
        custom_training_job_specs: Specifies the specs to run the training job with.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        vpc_connector: The name of the vpc connector to use.
    """
    generate(project_id, pipeline_params, af_registry_location,
             af_registry_name, base_image, cb_trigger_location, cb_trigger_name,
             cloud_run_location, cloud_run_name, cloud_tasks_queue_location,
             cloud_tasks_queue_name, csr_branch_name, csr_name,
             custom_training_job_specs, gs_bucket_location, gs_bucket_name,
             pipeline_runner_sa, run_local, schedule_location,
             schedule_name, schedule_pattern, vpc_connector)
    run(run_local)

def generate(project_id: str,
             pipeline_params: Dict,
             af_registry_location: Optional[str] = 'us-central1',
             af_registry_name: Optional[str] = 'vertex-mlops-af',
             base_image: Optional[str] = 'python:3.9-slim',
             cb_trigger_location: Optional[str] = 'us-central1',
             cb_trigger_name: Optional[str] = 'automlops-trigger',
             cloud_run_location: Optional[str] = 'us-central1',
             cloud_run_name: Optional[str] = 'run-pipeline',
             cloud_tasks_queue_location: Optional[str] = 'us-central1',
             cloud_tasks_queue_name: Optional[str] = 'queueing-svc',
             csr_branch_name: Optional[str] = 'automlops',
             csr_name: Optional[str] = 'AutoMLOps-repo',
             custom_training_job_specs: Optional[List[Dict]] = None,
             gs_bucket_location: Optional[str] = 'us-central1',
             gs_bucket_name: Optional[str] = None,
             pipeline_runner_sa: Optional[str] = None,
             run_local: Optional[bool] = True,
             schedule_location: Optional[str] = 'us-central1',
             schedule_name: Optional[str] = 'AutoMLOps-schedule',
             schedule_pattern: Optional[str] = 'No Schedule Specified',
             vpc_connector: Optional[str] = 'No VPC Specified'):
    """Generates relevant pipeline and component artifacts.

    Args: See go() function.
    """
    # Validate that run_local=False if schedule_pattern parameter is set
    validate_schedule(schedule_pattern, run_local)

    # Set defaults if none were given for bucket name and pipeline runner sa
    default_bucket_name = f'{project_id}-bucket' if gs_bucket_name is None else gs_bucket_name
    default_pipeline_runner_sa = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com' if pipeline_runner_sa is None else pipeline_runner_sa

    # Make necessary directories
    make_dirs(GENERATED_DIRS)

    # Switch statement to go here for different frameworks and deployments:

    # Build files required to run a Kubeflow Pipeline
    KfpBuilder.build(project_id, pipeline_params, af_registry_location,
        af_registry_name, base_image, cb_trigger_location, cb_trigger_name,
        cloud_run_location, cloud_run_name, cloud_tasks_queue_location,
        cloud_tasks_queue_name, csr_branch_name, csr_name,
        custom_training_job_specs, gs_bucket_location, default_bucket_name,
        default_pipeline_runner_sa, run_local, schedule_location,
        schedule_name, schedule_pattern, vpc_connector)

    CloudBuildBuilder.build(af_registry_location, af_registry_name, cloud_run_location,
        cloud_run_name, default_pipeline_runner_sa, project_id,
        run_local, schedule_pattern, vpc_connector)

def run(run_local: bool):
    """Builds, compiles, and submits the PipelineJob.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    # Build resources
    execute_process('./' + GENERATED_RESOURCES_SH_FILE, to_null=False)

    # Build, compile, and submit pipeline job
    if run_local:
        os.chdir(BASE_DIR)
        try:
            subprocess.run(['./scripts/run_all.sh'], shell=True, check=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.info(e)
        os.chdir('../')
    else:
        _push_to_csr()

    # Log generated resources
    _resources_generation_manifest(run_local)

def _resources_generation_manifest(run_local: bool):
    """Logs urls of generated resources.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    logging.info('\n'
        '#################################################################\n'
        '#                                                               #\n'
        '#                       RESOURCES MANIFEST                      #\n'
        '#---------------------------------------------------------------#\n'
        '#     Generated resources can be found at the following urls    #\n'
        '#                                                               #\n'
        '#################################################################\n')
    # pylint: disable=logging-fstring-interpolation
    logging.info(f'''Google Cloud Storage Bucket: https://console.cloud.google.com/storage/{defaults['gcp']['gs_bucket_name']}''')
    logging.info(f'''Artifact Registry: https://console.cloud.google.com/artifacts/docker/{defaults['gcp']['project_id']}/{defaults['gcp']['af_registry_location']}/{defaults['gcp']['af_registry_name']}''')
    logging.info(f'''Service Accounts: https://console.cloud.google.com/iam-admin/serviceaccounts?project={defaults['gcp']['project_id']}''')
    logging.info('APIs: https://console.cloud.google.com/apis')
    logging.info(f'''Cloud Source Repository: https://source.cloud.google.com/{defaults['gcp']['project_id']}/{defaults['gcp']['cloud_source_repository']}/+/{defaults['gcp']['cloud_source_repository_branch']}:''')
    logging.info(f'''Cloud Build Jobs: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['cb_trigger_location']}''')
    logging.info('Vertex AI Pipeline Runs: https://console.cloud.google.com/vertex-ai/pipelines/runs')
    if not run_local:
        logging.info(f'''Cloud Build Trigger: https://console.cloud.google.com/cloud-build/triggers;region={defaults['gcp']['cb_trigger_location']}''')
        logging.info(f'''Cloud Run Service: https://console.cloud.google.com/run/detail/{defaults['gcp']['cloud_run_location']}/{defaults['gcp']['cloud_run_name']}''')
        logging.info(f'''Cloud Tasks Queue: https://console.cloud.google.com/cloudtasks/queue/{defaults['gcp']['cloud_tasks_queue_location']}/{defaults['gcp']['cloud_tasks_queue_name']}/tasks''')
    if defaults['gcp']['cloud_schedule_pattern'] != 'No Schedule Specified':
        logging.info('Cloud Scheduler Job: https://console.cloud.google.com/cloudscheduler')

def _push_to_csr():
    """Initializes a git repo if one doesn't already exist,
       then pushes to the specified branch and triggers the cloudbuild job.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    csr_remote_origin_url = f'''https://source.developers.google.com/p/{defaults['gcp']['project_id']}/r/{defaults['gcp']['cloud_source_repository']}'''

    if not os.path.exists('.git'):

        # Initialize git and configure credentials
        execute_process('git init', to_null=False)
        execute_process('''git config --global credential.'https://source.developers.google.com'.helper gcloud.sh''', to_null=False)

        # Add repo and branch
        execute_process(f'''git remote add origin {csr_remote_origin_url}''', to_null=False)
        execute_process(f'''git checkout -B {defaults['gcp']['cloud_source_repository_branch']}''', to_null=False)
        has_remote_branch = subprocess.check_output([f'''git ls-remote origin {defaults['gcp']['cloud_source_repository_branch']}'''], shell=True, stderr=subprocess.STDOUT)

        # This will initialize the branch, a second push will be required to trigger the cloudbuild job after initializing
        if not has_remote_branch:
            execute_process('touch .gitkeep', to_null=False) # needed to keep dir here
            execute_process('git add .gitkeep', to_null=False)
            execute_process('''git commit -m 'init' ''', to_null=False)
            execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)

    # Check for remote origin url mismatch
    actual_remote = subprocess.check_output(['git config --get remote.origin.url'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
    if actual_remote != csr_remote_origin_url:
        raise RuntimeError(f'Expected remote origin url {csr_remote_origin_url} but found {actual_remote}. Reset your remote origin url to continue.')

    # Add, commit, and push changes to CSR
    execute_process('git add .', to_null=False)
    execute_process('''git commit -m 'Run AutoMLOps' ''', to_null=False)
    execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)
    # pylint: disable=logging-fstring-interpolation
    logging.info(f'''Pushing code to {defaults['gcp']['cloud_source_repository_branch']} branch, triggering cloudbuild...''')
    logging.info(f'''Cloudbuild job running at: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['cb_trigger_location']}''')

def component(func: Optional[Callable] = None,
              *,
              packages_to_install: Optional[List[str]] = None):
    """Decorator for Python-function based components in AutoMLOps.

    Example usage:
    from AutoMLOps import AutoMLOps
    @AutoMLOps.component
    def my_function_one(input: str, output: Output[Model]):
      ...
    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install: A list of optional packages to install before
            executing func. These will always be installed at component runtime.
  """
    if func is None:
        return functools.partial(
            component,
            packages_to_install=packages_to_install)
    else:
        return KfpScaffold.create_component_scaffold(
            func=func,
            packages_to_install=packages_to_install)

def pipeline(func: Optional[Callable] = None,
             *,
             name: Optional[str] = None,
             description: Optional[str] = None):
    """Decorator for Python-function based pipelines in AutoMLOps.

    Example usage:
    from AutoMLOps import AutoMLOps
    @AutoMLOps.pipeline
    def pipeline(bq_table: str,
                output_model_directory: str,
                project: str,
                region: str,
                ):

        dataset_task = create_dataset(
            bq_table=bq_table, 
            project=project)
      ...
    Args:
        func: The python function to create a pipeline from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
  """
    if func is None:
        return functools.partial(
            pipeline,
            name=name,
            description=description)
    else:
        return KfpScaffold.create_pipeline_scaffold(
            func=func,
            name=name,
            description=description)

def clear_cache():
    """Deletes all temporary files stored in the cache directory."""
    execute_process(f'rm -rf {OUTPUT_DIR}', to_null=False)
    make_dirs([OUTPUT_DIR])
    logging.info('Cache cleared.')
