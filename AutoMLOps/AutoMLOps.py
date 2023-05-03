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

import functools
import logging
import os
import re
import sys
import subprocess
from typing import Callable, Dict, List, Optional

from AutoMLOps import BuilderUtils
from AutoMLOps import ComponentBuilder
from AutoMLOps import PipelineBuilder
from AutoMLOps import CloudRunBuilder
from AutoMLOps import ScriptsBuilder

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

TOP_LVL_NAME = 'AutoMLOps/'
DEFAULTS_FILE = TOP_LVL_NAME + 'configs/defaults.yaml'
PIPELINE_SPEC_SH_FILE = TOP_LVL_NAME + 'scripts/build_pipeline_spec.sh'
BUILD_COMPONENTS_SH_FILE = TOP_LVL_NAME + 'scripts/build_components.sh'
RUN_PIPELINE_SH_FILE = TOP_LVL_NAME + 'scripts/run_pipeline.sh'
RUN_ALL_SH_FILE = TOP_LVL_NAME + 'scripts/run_all.sh'
RESOURCES_SH_FILE = TOP_LVL_NAME + 'scripts/create_resources.sh'
SUBMIT_JOB_FILE = TOP_LVL_NAME + 'scripts/submit_to_runner_svc.sh'
CLOUDBUILD_FILE = TOP_LVL_NAME + 'cloudbuild.yaml'
PIPELINE_FILE = TOP_LVL_NAME + 'pipelines/pipeline.py'
DEFAULT_IMAGE = 'python:3.9-slim'
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

def go(project_id: str,
       pipeline_params: Dict,
       af_registry_location: Optional[str] = 'us-central1',
       af_registry_name: Optional[str] = 'vertex-mlops-af',
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
       use_kfp_spec: Optional[bool] = False,
       vpc_connector: Optional[str] = 'No VPC Specified'):
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
        use_kfp_spec: Flag that determines the format of the component yamls.
        vpc_connector: The name of the vpc connector to use.
    """
    generate(project_id, pipeline_params, af_registry_location,
             af_registry_name, cb_trigger_location, cb_trigger_name,
             cloud_run_location, cloud_run_name, cloud_tasks_queue_location,
             cloud_tasks_queue_name, csr_branch_name, csr_name,
             custom_training_job_specs, gs_bucket_location, gs_bucket_name,
             pipeline_runner_sa, run_local, schedule_location,
             schedule_name, schedule_pattern, use_kfp_spec,
             vpc_connector)
    run(run_local)

def generate(project_id: str,
             pipeline_params: Dict,
             af_registry_location: Optional[str] = 'us-central1',
             af_registry_name: Optional[str] = 'vertex-mlops-af',
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
             use_kfp_spec: Optional[bool] = False,
             vpc_connector: Optional[str] = 'No VPC Specified'):
    """Generates relevant pipeline and component artifacts.

    Args: See go() function.
    """
    # Validate cloud schedule pattern as a correctly formatted cron job
    BuilderUtils.validate_schedule(schedule_pattern, run_local)

    # Set defaults if none were given for bucket name and pipeline runner sa
    default_bucket_name = f'{project_id}-bucket' if gs_bucket_name is None else gs_bucket_name
    default_pipeline_runner_sa = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com' if pipeline_runner_sa is None else pipeline_runner_sa

    # Make necessary directories
    BuilderUtils.make_dirs(DIRS)

    # Initialize AutoMLOps scripts builder
    automlops_scripts = ScriptsBuilder.AutoMLOps(
        af_registry_location, af_registry_name, cb_trigger_location,
        cb_trigger_name, cloud_run_location, cloud_run_name,
        cloud_tasks_queue_location, cloud_tasks_queue_name, csr_branch_name,
        csr_name, gs_bucket_location, default_bucket_name, DEFAULT_IMAGE,
        default_pipeline_runner_sa, project_id, run_local, schedule_location,
        schedule_name, schedule_pattern, TOP_LVL_NAME, vpc_connector)

    # Write defaults.yaml
    BuilderUtils.write_file(DEFAULTS_FILE, automlops_scripts.defaults, 'w+')

    # Write scripts for building pipeline, building components, running pipeline, and running all files
    BuilderUtils.write_and_chmod(PIPELINE_SPEC_SH_FILE, automlops_scripts.build_pipeline_spec)
    BuilderUtils.write_and_chmod(BUILD_COMPONENTS_SH_FILE, automlops_scripts.build_components)
    BuilderUtils.write_and_chmod(RUN_PIPELINE_SH_FILE, automlops_scripts.run_pipeline)
    BuilderUtils.write_and_chmod(RUN_ALL_SH_FILE, automlops_scripts.run_all)

    # Write scripts to create resources and cloud build config
    BuilderUtils.write_and_chmod(RESOURCES_SH_FILE, automlops_scripts.create_resources_script)
    BuilderUtils.write_file(CLOUDBUILD_FILE, automlops_scripts.create_cloudbuild_config, 'w+')

    # Copy tmp pipeline file over to AutoMLOps directory
    BuilderUtils.execute_process(f'cp {BuilderUtils.PIPELINE_TMPFILE} {PIPELINE_FILE}', to_null=False)

    # Create components and pipelines
    components_path_list = BuilderUtils.get_components_list()
    for path in components_path_list:
        ComponentBuilder.formalize(path, TOP_LVL_NAME, DEFAULTS_FILE, use_kfp_spec)
    PipelineBuilder.formalize(custom_training_job_specs, DEFAULTS_FILE, pipeline_params, TOP_LVL_NAME)

    # Write requirements file
    _create_requirements()

    # Write dockerfile to the component base directory
    BuilderUtils.write_file(f'{COMPONENT_BASE}/Dockerfile', automlops_scripts.dockerfile, 'w')

    # If this is being run in the cloud, formalize the cloud run process
    if not run_local:
        CloudRunBuilder.formalize(TOP_LVL_NAME, DEFAULTS_FILE)

def run(run_local: bool):
    """Builds, compiles, and submits the PipelineJob.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    BuilderUtils.execute_process('./'+RESOURCES_SH_FILE, to_null=False)
    if run_local:
        os.chdir(TOP_LVL_NAME)
        try:
            subprocess.run(['./scripts/run_all.sh'], shell=True, check=True,
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.info(e)
        os.chdir('../')
    else:
        _push_to_csr()
    _resources_generation_manifest(run_local)

def _resources_generation_manifest(run_local: bool):
    """Logs urls of generated resources.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
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
    defaults = BuilderUtils.read_yaml_file(DEFAULTS_FILE)
    if not os.path.exists('.git'):
        BuilderUtils.execute_process('git init', to_null=False)
        BuilderUtils.execute_process('''git config --global credential.'https://source.developers.google.com'.helper gcloud.sh''', to_null=False)
        BuilderUtils.execute_process(f'''git remote add origin https://source.developers.google.com/p/{defaults['gcp']['project_id']}/r/{defaults['gcp']['cloud_source_repository']}''', to_null=False)
        BuilderUtils.execute_process(f'''git checkout -B {defaults['gcp']['cloud_source_repository_branch']}''', to_null=False)
        has_remote_branch = subprocess.check_output([f'''git ls-remote origin {defaults['gcp']['cloud_source_repository_branch']}'''], shell=True, stderr=subprocess.STDOUT)
        if not has_remote_branch:
            # This will initialize the branch, a second push will be required to trigger the cloudbuild job after initializing
            BuilderUtils.execute_process('touch .gitkeep', to_null=False) # needed to keep dir here
            BuilderUtils.execute_process('git add .gitkeep', to_null=False)
            BuilderUtils.execute_process('''git commit -m 'init' ''', to_null=False)
            BuilderUtils.execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)

    BuilderUtils.execute_process(f'touch {TOP_LVL_NAME}scripts/pipeline_spec/.gitkeep', to_null=False) # needed to keep dir here
    BuilderUtils.execute_process('git add .', to_null=False)
    BuilderUtils.execute_process('''git commit -m 'Run AutoMLOps' ''', to_null=False)
    BuilderUtils.execute_process(f'''git push origin {defaults['gcp']['cloud_source_repository_branch']} --force''', to_null=False)
    # pylint: disable=logging-fstring-interpolation
    logging.info(f'''Pushing code to {defaults['gcp']['cloud_source_repository_branch']} branch, triggering cloudbuild...''')
    logging.info(f'''Cloudbuild job running at: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['cb_trigger_location']}''')

def _create_requirements():
    """Writes a requirements.txt to the component_base directory.
       Infers pip requirements from the python srcfiles using 
       pipreqs. Takes user-inputted requirements, and addes some 
       default gcp packages as well as packages that are often missing
       in setup.py files (e.g db_types, pyarrow, gcsfs, fsspec).
    """
    reqs_filename = f'{COMPONENT_BASE}/requirements.txt'
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
    BuilderUtils.execute_process(f'python3 -m pipreqs.pipreqs {COMPONENT_BASE} --mode no-pin --force', to_null=False)
    pipreqs = BuilderUtils.read_file(reqs_filename).splitlines()
    # Get user-inputted requirements from .tmpfiles dir
    user_inp_reqs = []
    components_path_list = BuilderUtils.get_components_list()
    for component_path in components_path_list:
        component_spec = BuilderUtils.read_yaml_file(component_path)
        reqs = component_spec['implementation']['container']['command'][2]
        formatted_reqs = re.findall('\'([^\']*)\'', reqs)
        user_inp_reqs.extend(formatted_reqs)
    # Remove duplicates
    set_of_requirements = set(pipreqs + user_inp_reqs + default_gcp_reqs)
    reqs_str = ''.join(r+'\n' for r in sorted(set_of_requirements))
    BuilderUtils.delete_file(reqs_filename)
    BuilderUtils.write_file(reqs_filename, reqs_str, 'w')

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
        ComponentBuilder.create_component_scaffold(
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
        PipelineBuilder.create_pipeline_scaffold(
            func=func,
            name=name,
            description=description)
