# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Utility functions and globals to be used by all
   other modules in this directory."""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught

import inspect
import itertools
import json
import logging
import os
import subprocess
import textwrap
from typing import Callable

from packaging import version
import yaml
from jinja2 import Template

from googleapiclient import discovery
import google.auth

from google_cloud_automlops.utils.constants import (
    CACHE_DIR,
    DEFAULT_SCHEDULE_PATTERN,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_JOB_SPEC_PATH,
    IAM_ROLES_RUNNER_SA,
    MIN_GCLOUD_BETA_VERSION,
    MIN_GCLOUD_SDK_VERSION,
    MIN_RECOMMENDED_TERRAFORM_VERSION,
    PLACEHOLDER_IMAGE
)

from google_cloud_automlops.utils.enums import (
    Orchestrator,
    PipelineJobSubmitter
)

from google_cloud_automlops.deployments.enums import (
    ArtifactRepository,
    CodeRepository,
    Deployer
)
from google_cloud_automlops.provisioning.enums import Provisioner


def make_dirs(directories: list):
    """Makes directories with the specified names.

    Args:
        directories (list): Path of the directories to make.
    """
    for d in directories:
        try:
            os.makedirs(d)
        except FileExistsError:
            pass


def read_yaml_file(filepath: str) -> dict:
    """Reads a yaml and returns file contents as a dict. Defaults to utf-8 encoding.

    Args:
        filepath (str): Path to the yaml.

    Returns:
        dict: Contents of the yaml.

    Raises:
        Exception: If an error is encountered reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            file_dict = yaml.safe_load(file)
        file.close()
    except yaml.YAMLError as err:
        raise yaml.YAMLError(f'Error reading file. {err}') from err
    return file_dict


def write_yaml_file(filepath: str, contents: dict, mode: str):
    """Writes a dictionary to yaml. Defaults to utf-8 encoding.

    Args:
        filepath (str): Path to the file.
        contents (dict): Dictionary to be written to yaml.
        mode (str): Read/write mode to be used.

    Raises:
        Exception: An error is encountered while writing the file.
    """
    try:
        with open(filepath, mode, encoding='utf-8') as file:
            yaml.safe_dump(contents, file, sort_keys=False)
        file.close()
    except yaml.YAMLError as err:
        raise yaml.YAMLError(f'Error writing to file. {err}') from err


def read_file(filepath: str) -> str:
    """Reads a file and returns contents as a string. Defaults to utf-8 encoding.

    Args:
        filepath (str): Path to the file.

    Returns:
        str: Contents of the file.

    Raises:
        Exception: An error is encountered while reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            contents = file.read()
        file.close()
    except FileNotFoundError as err:
        raise FileNotFoundError(f'Error reading file. {err}') from err
    return contents


def write_file(filepath: str, text: str, mode: str):
    """Writes a file at the specified path. Defaults to utf-8 encoding.

    Args:
        filepath (str): Path to the file.
        text (str): Text to be written to file.
        mode (str): Read/write mode to be used.

    Raises:
        Exception: An error is encountered writing the file.
    """
    try:
        with open(filepath, mode, encoding='utf-8') as file:
            file.write(text)
        file.close()
    except OSError as err:
        raise OSError(f'Error writing to file. {err}') from err


def write_and_chmod(filepath: str, text: str):
    """Writes a file at the specified path and chmods the file to allow for execution.

    Args:
        filepath (str): Path to the file.
        text (str): Text to be written to file.

    Raises:
        Exception: An error is encountered while chmod-ing the file.
    """
    write_file(filepath, text, 'w')
    try:
        st = os.stat(filepath)
        os.chmod(filepath, st.st_mode | 0o111)
    except OSError as err:
        raise OSError(f'Error chmod-ing file. {err}') from err


def delete_file(filepath: str):
    """Deletes a file at the specified path. If it does not exist, pass.

    Args:
        filepath (str): Path to the file.
    """
    try:
        os.remove(filepath)
    except OSError:
        pass


def get_components_list(full_path: bool = True) -> list:
    """Reads yamls in the cache directory, verifies they are component yamls, and returns the name
    of the files.

    Args:
        full_path (bool): If false, stores only the filename w/o extension.

    Returns:
        list: Contains the names or paths of all component yamls in the dir.
    """
    components_list = []
    elements = os.listdir(CACHE_DIR)
    for file in list(filter(lambda y: ('.yaml' or '.yml') in y, elements)):
        path = os.path.join(CACHE_DIR, file)
        if is_component_config(path):
            if full_path:
                components_list.append(path)
            else:
                components_list.append(os.path.basename(file).split('.')[0])
    return components_list


def is_component_config(filepath: str) -> bool:
    """Checks to see if the given file is a component yaml.

    Args:
        filepath (str): Path to a yaml file.

    Returns:
        bool: Whether the given file is a component yaml.
    """
    required_keys = ['name','inputs','implementation']
    file_dict = read_yaml_file(filepath)
    return all(key in file_dict.keys() for key in required_keys)


def execute_process(command: str, to_null: bool):
    """Executes an external shell process.

    Args:
        command (str): Command to execute.
        to_null (bool): Determines where to send output.

    Raises:
        Exception: An error occured while executing the script.
    """
    stdout = subprocess.DEVNULL if to_null else None
    try:
        subprocess.run([command],
                       shell=True,
                       check=True,
                       stdout=stdout,
                       stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f'Error executing process. {err}') from err


def validate_use_ci(setup_model_monitoring: bool, schedule_pattern: str, use_ci: str):
    """Validates that the inputted schedule parameter and model_monitoring parameter align with the 
    use_ci configuration.

    Note: this function does not validate that schedule_pattern is a properly formatted cron value.
    Cron format validation is done in the backend by GCP.
    
    Args:
        setup_model_monitoring (bool): Specifies whether to set up a Vertex AI Model Monitoring Job.
        schedule_pattern (str): Cron formatted value used to create a Scheduled retrain job.
        use_ci (bool): Specifies whether to use Cloud CI/CD.

    Raises:
        Exception: use_ci validation failed.
    """
    if setup_model_monitoring and not use_ci:
        raise ValueError('use_ci must be set to True to use Model Monitoring.')
    if schedule_pattern != DEFAULT_SCHEDULE_PATTERN and not use_ci:
        raise ValueError('use_ci must be set to True to use Cloud Scheduler.')


def get_function_source_definition(func: Callable) -> str:
    """Returns a formatted string of the source code.

    Args:
        func (Callable): The python function to create a component from. The function should have
            type annotations for all its arguments, indicating how it is intended to be used (e.g.
            as an input/output Artifact object, a plain parameter, or a path to a file).

    Returns:
        str: The source code from the inputted function.

    Raises:
        Exception: The preprocess operations failed.
    """
    source_code = inspect.getsource(func)
    source_code = textwrap.dedent(source_code)
    source_code_lines = source_code.split('\n')
    source_code_lines = itertools.dropwhile(lambda x: not x.startswith('def'),
                                            source_code_lines)
    if not source_code_lines:
        raise ValueError(
            f'Failed to dedent and clean up the source of function "{func.__name__}". '
            f'It is probably not properly indented.')

    return '\n'.join(source_code_lines)


def stringify_job_spec_list(job_spec_list: list) -> list:
    """Takes in a list of job spec dictionaries and turns them into strings.

    Args:
        job_spec (list): Dictionary with job spec info. e.g.
            custom_training_job_specs = [{
                'component_spec': 'train_model',
                'display_name': 'train-model-accelerated',
                'machine_type': 'a2-highgpu-1g',
                'accelerator_type': 'NVIDIA_TESLA_A100',
                'accelerator_count': 1
            }]

    Returns:
        list[str]: Python formatted dictionary code.
    """
    if not job_spec_list:
        return None
    output = []
    for spec in job_spec_list:
        mapping = {}
        if isinstance(spec['component_spec'], str):
            mapping['component_spec'] = spec['component_spec']
        else:
            raise ValueError('component_spec must be a string.')
        # Remove string quotes from component spec line
        mapping['spec_string'] = json.dumps(spec, sort_keys=True, indent=8).replace(f'''"{spec['component_spec']}"''', f'''{spec['component_spec']}''')
        mapping['spec_string'] = mapping['spec_string'].replace('}', '    }') # align closing bracket
        output.append(mapping)
    return output

def is_using_kfp_spec(image: str) -> bool:
    """Takes in an image string from a component yaml and determines if it came from kfp or not.

    Args:
        image (str): Image string. #TODO: make this more informative

    Returns:
        bool: Whether the component using kfp spec.
    """
    return image != PLACEHOLDER_IMAGE


def create_default_config(artifact_repo_location: str,
                          artifact_repo_name: str,
                          artifact_repo_type: str,
                          base_image: str,
                          build_trigger_location: str,
                          build_trigger_name: str,
                          deployment_framework: str,
                          naming_prefix: str,
                          orchestration_framework: str,
                          pipeline_job_runner_service_account: str,
                          pipeline_job_submission_service_location: str,
                          pipeline_job_submission_service_name: str,
                          pipeline_job_submission_service_type: str,
                          project_id: str,
                          provisioning_framework: str,
                          pubsub_topic_name: str,
                          schedule_location: str,
                          schedule_name: str,
                          schedule_pattern: str,
                          setup_model_monitoring: bool,
                          source_repo_branch: str,
                          source_repo_name: str,
                          source_repo_type: str,
                          storage_bucket_location: str,
                          storage_bucket_name: str,
                          use_ci: bool,
                          vpc_connector: str) -> dict:
    """Creates defaults.yaml file contents as a dict. This defaults file is used by subsequent
    functions and by the pipeline files themselves.

    Args:
        artifact_repo_location (str): Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name (str): Artifact repo name where components are stored (default use with
            Artifact Registry).
        artifact_repo_type (str): Type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        base_image (str): Image to use in the component base dockerfile.
        build_trigger_location (str): Location of the build trigger (for cloud build).
        build_trigger_name (str): Name of the build trigger (for cloud build).
        deployment_framework (str): Name of CI tool to use (e.g. cloud build, github actions, etc.)
        naming_prefix (str): Unique value used to differentiate pipelines and services across
            AutoMLOps runs.
        orchestration_framework (str): Orchestration framework to use (e.g. kfp, tfx, etc.)
        pipeline_job_runner_service_account (str): Service Account to run PipelineJobs.
        pipeline_job_submission_service_location (str): Location of the cloud submission service.
        pipeline_job_submission_service_name (str): Name of the cloud submission service.
        pipeline_job_submission_service_type (str): Tool to host for the cloud submission service
            (e.g. cloud run, cloud functions).
        project_id (str): The project ID.
        provisioning_framework (str): IaC tool to use (e.g. Terraform, Pulumi, etc.)
        pubsub_topic_name (str): Name of the pubsub topic to publish to.
        schedule_location (str): Location of the scheduler resource.
        schedule_name (str): Name of the scheduler resource.
        schedule_pattern (str): Cron formatted value used to create a Scheduled retrain job.
        setup_model_monitoring (bool): Specifies whether to set up a Vertex AI Model Monitoring Job.
        source_repo_branch (str): Branch to use in the source repository.
        source_repo_name (str): Name of the source repository to use.
        source_repo_type (str): Type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location (str): Region of the GS bucket.
        storage_bucket_name (str): GS bucket name where pipeline run metadata is stored.
        use_ci (bool): Specifies whether to use Cloud CI/CD.
        vpc_connector (str): Name of the vpc connector to use.

    Returns:
        dict: Defaults yaml file content.
    """
    defaults = {}
    defaults['gcp'] = {}
    defaults['gcp']['artifact_repo_location'] = artifact_repo_location
    defaults['gcp']['artifact_repo_name'] = artifact_repo_name
    defaults['gcp']['artifact_repo_type'] = artifact_repo_type
    defaults['gcp']['base_image'] = base_image
    if use_ci:
        defaults['gcp']['build_trigger_location'] = build_trigger_location
        defaults['gcp']['build_trigger_name'] = build_trigger_name
    defaults['gcp']['naming_prefix'] = naming_prefix
    defaults['gcp']['pipeline_job_runner_service_account'] = pipeline_job_runner_service_account
    if use_ci:
        defaults['gcp']['pipeline_job_submission_service_location'] = pipeline_job_submission_service_location
        defaults['gcp']['pipeline_job_submission_service_name'] = pipeline_job_submission_service_name
        defaults['gcp']['pipeline_job_submission_service_type'] = pipeline_job_submission_service_type
    defaults['gcp']['project_id'] = project_id
    defaults['gcp']['setup_model_monitoring'] = setup_model_monitoring
    if use_ci:
        defaults['gcp']['pubsub_topic_name'] = pubsub_topic_name
        defaults['gcp']['schedule_location'] = schedule_location
        defaults['gcp']['schedule_name'] = schedule_name
        defaults['gcp']['schedule_pattern'] = schedule_pattern
        defaults['gcp']['source_repository_branch'] = source_repo_branch
        defaults['gcp']['source_repository_name'] = source_repo_name
        defaults['gcp']['source_repository_type'] = source_repo_type
    defaults['gcp']['storage_bucket_location'] = storage_bucket_location
    defaults['gcp']['storage_bucket_name'] = storage_bucket_name
    if use_ci:
        defaults['gcp']['vpc_connector'] = vpc_connector

    defaults['pipelines'] = {}
    defaults['pipelines']['gs_pipeline_job_spec_path'] = f'gs://{storage_bucket_name}/pipeline_root/{naming_prefix}/pipeline_job.json'
    defaults['pipelines']['parameter_values_path'] = GENERATED_PARAMETER_VALUES_PATH
    defaults['pipelines']['pipeline_component_directory'] = 'components'
    defaults['pipelines']['pipeline_job_spec_path'] = GENERATED_PIPELINE_JOB_SPEC_PATH
    defaults['pipelines']['pipeline_region'] = storage_bucket_location
    defaults['pipelines']['pipeline_storage_path'] = f'gs://{storage_bucket_name}/pipeline_root'

    defaults['tooling'] = {}
    defaults['tooling']['deployment_framework'] = deployment_framework
    defaults['tooling']['provisioning_framework'] = provisioning_framework
    defaults['tooling']['orchestration_framework'] = orchestration_framework
    defaults['tooling']['use_ci'] = use_ci

    if setup_model_monitoring:
        # These fields will be set up if and when AutoMLOps.monitor() is called
        defaults['monitoring'] = {}
        defaults['monitoring']['target_field'] = None
        defaults['monitoring']['model_endpoint'] = None
        defaults['monitoring']['alert_emails'] = None
        defaults['monitoring']['auto_retraining_params'] = None
        defaults['monitoring']['drift_thresholds'] = None
        defaults['monitoring']['gs_auto_retraining_params_path'] = None
        defaults['monitoring']['job_display_name'] = None
        defaults['monitoring']['log_sink_name'] = None
        defaults['monitoring']['monitoring_interval'] = None
        defaults['monitoring']['monitoring_location'] = None
        defaults['monitoring']['sample_rate'] = None
        defaults['monitoring']['skew_thresholds'] = None
        defaults['monitoring']['training_dataset'] = None

    return defaults


def get_required_apis(defaults: dict) -> list:
    """Returns the list of required APIs based on the user tooling selection determined during
    the generate() step.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Required APIs.
    """
    required_apis = [
        'cloudbuild.googleapis.com',
        'cloudresourcemanager.googleapis.com',
        'compute.googleapis.com',
        'iamcredentials.googleapis.com',
        'iam.googleapis.com',
        'pubsub.googleapis.com',
        'storage.googleapis.com']
    if defaults['tooling']['orchestration_framework'] == Orchestrator.KFP.value:
        required_apis.append('aiplatform.googleapis.com')
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        required_apis.append('artifactregistry.googleapis.com')
    # if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
    #     required_apis.add('cloudbuild.googleapis.com')
    if defaults['tooling']['use_ci']:
        if defaults['gcp']['schedule_pattern'] != DEFAULT_SCHEDULE_PATTERN:
            required_apis.append('cloudscheduler.googleapis.com')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            required_apis.append('run.googleapis.com')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            required_apis.append('cloudfunctions.googleapis.com')
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            required_apis.append('sourcerepo.googleapis.com')
        if defaults['gcp']['setup_model_monitoring']:
            required_apis.append('logging.googleapis.com')
    return required_apis


def get_provision_min_permissions(defaults: dict) -> list:
    """Returns the list of minimum required permissions to run the provision() step based on the
    user tooling selection determined during the generate() step.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Required permissions.
    """
    required_permissions = [
        'serviceusage.services.enable',
        'serviceusage.services.use',
        'resourcemanager.projects.setIamPolicy',
        'iam.serviceAccounts.list',
        'iam.serviceAccounts.create',
        'iam.serviceAccounts.actAs',
        'storage.buckets.get',
        'storage.buckets.create']
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        required_permissions.extend(['artifactregistry.repositories.list', 'artifactregistry.repositories.create'])
    if defaults['tooling']['use_ci']:
        required_permissions.extend(['pubsub.topics.list', 'pubsub.topics.create',
                                     'pubsub.subscriptions.list', 'pubsub.subscriptions.create'])
        if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
            required_permissions.extend(['cloudbuild.builds.list', 'cloudbuild.builds.create'])
        if defaults['gcp']['schedule_pattern'] != DEFAULT_SCHEDULE_PATTERN:
            required_permissions.extend(['cloudscheduler.jobs.list', 'cloudscheduler.jobs.create'])
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            required_permissions.extend(['run.services.get', 'run.services.create'])
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            required_permissions.extend(['cloudfunctions.functions.get', 'cloudfunctions.functions.create'])
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            required_permissions.extend(['source.repos.list', 'source.repos.create'])
    return required_permissions


def get_provision_recommended_roles(defaults: dict) -> list:
    """Creates the list of recommended roles to run the provision() step based on the user tooling
    selection determined during the generate() step. These roles have the minimum permissions
    required for provision.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Recommended provision roles.
    """
    recommended_roles = [
        'roles/serviceusage.serviceUsageAdmin',
        'roles/resourcemanager.projectIamAdmin',
        'roles/iam.serviceAccountAdmin',
        'roles/iam.serviceAccountUser',
        'roles/storage.admin']
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        recommended_roles.append('roles/artifactregistry.admin')
    if defaults['tooling']['use_ci']:
        recommended_roles.append('roles/pubsub.editor')
        if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
            recommended_roles.append('roles/cloudbuild.builds.editor')
        if defaults['gcp']['schedule_pattern'] != DEFAULT_SCHEDULE_PATTERN:
            recommended_roles.append('roles/cloudscheduler.admin')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            recommended_roles.append('roles/run.admin')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            recommended_roles.append('roles/cloudfunctions.admin')
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            recommended_roles.append('roles/source.admin')
    return recommended_roles


def get_deploy_with_precheck_min_permissions(defaults: dict) -> list:
    """Creates the list of minimum required permissions to run the deploy() step based on the user
    tooling selection, determined during the generate() step. This function is called when
    precheck=True, which makes several API calls to determine if the infra exists to run deploy()
    and increases the required list of permissions.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Minimum permissions to deploy with precheck=True.
    """
    recommended_permissions = [
        'serviceusage.services.get',
        'resourcemanager.projects.getIamPolicy',
        'storage.buckets.update',
        'iam.serviceAccounts.get']
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        recommended_permissions.append('artifactregistry.repositories.get')
    if defaults['tooling']['use_ci']:
        recommended_permissions.extend(['pubsub.topics.get', 'pubsub.subscriptions.get'])
        if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
            recommended_permissions.append('cloudbuild.builds.get')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            recommended_permissions.append('run.services.get')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            recommended_permissions.append('cloudfunctions.functions.get')
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            recommended_permissions.append('source.repos.update')
    elif not defaults['tooling']['use_ci']:
        recommended_permissions.extend(['cloudbuild.builds.get', 'aiplatform.pipelineJobs.create'])
    return recommended_permissions


def get_deploy_with_precheck_recommended_roles(defaults: dict) -> list:
    """Returns the list of recommended roles to run the deploy() step based on the user tooling
    selection determined during the generate() step. This function is called when precheck=True,
    which makes several API calls to determine if the infra exists to run deploy() and increases the
    required list of permissions.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Recommended roles to deploy with precheck=True.
    """
    recommended_roles = [
        'roles/serviceusage.serviceUsageViewer',
        'roles/iam.roleViewer',
        'roles/storage.admin',
        'roles/iam.serviceAccountUser']
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        recommended_roles.append('roles/artifactregistry.reader')
    if defaults['tooling']['use_ci']:
        recommended_roles.append('roles/pubsub.viewer')
        if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
            recommended_roles.append('roles/cloudbuild.builds.editor')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            recommended_roles.append('roles/run.viewer')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            recommended_roles.append('roles/cloudfunctions.viewer')
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            recommended_roles.append('roles/source.writer')
    elif not defaults['tooling']['use_ci']:
        recommended_roles.extend(['roles/cloudbuild.builds.editor', 'roles/aiplatform.user'])
    return recommended_roles


def get_deploy_without_precheck_min_permissions(defaults: dict) -> list:
    """Creates the list of minimum required permissions to run the deploy() step based on the user
    tooling selection determined during the generate() step. This function is called when
    precheck=False, which decreases the required list of permissions.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Minimum permissions to deploy with precheck=False.
    """
    recommended_permissions = []
    if defaults['tooling']['use_ci']:
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            recommended_permissions.append('source.repos.update')
    elif not defaults['tooling']['use_ci']:
        recommended_permissions.extend(['cloudbuild.builds.create', 'storage.buckets.update', 'aiplatform.pipelineJobs.create'])
    return recommended_permissions


def get_deploy_without_precheck_recommended_roles(defaults: dict) -> list:
    """Creates the list of recommended roles to run the deploy() step based on the user tooling
    selection determined during the generate() step. This function is called when precheck=False,
    which decreases the required list of permissions.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Recommended roles to deploy with precheck=False.
    """
    recommended_roles = []
    if defaults['tooling']['use_ci']:
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            recommended_roles.append('roles/source.writer')
    elif not defaults['tooling']['use_ci']:
        recommended_roles.extend(['roles/cloudbuild.builds.editor', 'roles/storage.admin', 'roles/aiplatform.user'])
    return recommended_roles


def get_model_monitoring_min_permissions(defaults: dict) -> list:
    """Creates the list of minimum required permissions to run the monitor() step based on the user
    tooling selection determined during the generate() step.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Minimum permissions to create a monitoring job.
    """
    recommended_permissions = [
        'aiplatform.endpoints.list',
        'aiplatform.modelDeploymentMonitoringJobs.list',
        'aiplatform.modelDeploymentMonitoringJobs.create',
        'aiplatform.modelDeploymentMonitoringJobs.update']
    if defaults['monitoring']['auto_retraining_params']:
        recommended_permissions.extend(['storage.buckets.update', 'logging.sinks.get', 'logging.sinks.create',
                                        'logging.sinks.update', 'iam.serviceAccounts.setIamPolicy'])
    return recommended_permissions


def get_model_monitoring_recommended_roles(defaults: dict) -> list:
    """Creates the list of recommended roles to run the monitor() step based on the user tooling
    selection determined during the generate() step.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).

    Returns:
        list: Recommended roles to create a monitoring job.
    """
    recommended_roles = ['roles/aiplatform.user']
    if defaults['monitoring']['auto_retraining_params']:
        recommended_roles.extend(['roles/storage.admin', 'roles/logging.configWriter', 'roles/iam.serviceAccountAdmin'])
    return recommended_roles


def account_permissions_warning(operation: str, defaults: dict):
    """Logs the current gcloud account and generates warnings based on the operation being performed.

    Args:
        operation (str): Specifies which operation is being performed. Available options {provision,
            deploy_with_precheck, deploy_without_precheck, model_monitoring}.
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).
    """
    bullet_nl = '\n-'
    gcp_account = subprocess.check_output(
        ['gcloud config list account --format "value(core.account)" 2> /dev/null'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
    if operation == 'provision':
        logging.warning(f'WARNING: Provisioning requires these permissions:\n-{bullet_nl.join(i for i in get_provision_min_permissions(defaults))}\n\n'
                        f'You are currently using: {gcp_account}. Please check your account permissions.\n'
                        f'The following are the recommended roles for provisioning:\n-{bullet_nl.join(i for i in get_provision_recommended_roles(defaults))}\n')

    elif operation == 'deploy_with_precheck':
        logging.warning(f'WARNING: Running precheck for deploying requires these permissions:\n-{bullet_nl.join(i for i in get_deploy_with_precheck_min_permissions(defaults))}\n\n'
                        f'You are currently using: {gcp_account}. Please check your account permissions.\n'
                        f'The following are the recommended roles for deploying with precheck:\n-{bullet_nl.join(i for i in get_deploy_with_precheck_recommended_roles(defaults))}\n')

    elif operation == 'deploy_without_precheck':
        logging.warning(f'WARNING: Deploying requires these permissions:\n-{bullet_nl.join(i for i in get_deploy_without_precheck_min_permissions(defaults))}\n\n'
                        f'You are currently using: {gcp_account}. Please check your account permissions.\n'
                        f'The following are the recommended roles for deploying:\n-{bullet_nl.join(i for i in get_deploy_without_precheck_recommended_roles(defaults))}\n')

    elif operation == 'model_monitoring':
        logging.warning(f'WARNING: Creating monitoring jobs requires these permissions:\n-{bullet_nl.join(i for i in get_model_monitoring_min_permissions(defaults))}\n\n'
                        f'You are currently using: {gcp_account}. Please check your account permissions.\n'
                        f'The following are the recommended roles for creating monitoring jobs:\n-{bullet_nl.join(i for i in get_model_monitoring_recommended_roles(defaults))}\n')


def check_installation_versions(provisioning_framework: str):
    """Checks the version of the provisioning tool (e.g. terraform, gcloud) and generates warning if
    either the tool is not installed, or if it below the recommended version.

    Args:
        provisioning_framework (str): The IaC tool to use (e.g. Terraform, Pulumi, etc.).
    """
    if provisioning_framework == Provisioner.GCLOUD.value:
        try:
            gcloud_sdk_version = subprocess.check_output(
                ['gcloud info --format="value(basic.version)" 2> /dev/null'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
            if version.parse(MIN_GCLOUD_SDK_VERSION) > version.parse(gcloud_sdk_version):
                logging.warning(f'WARNING: You are currently using version {gcloud_sdk_version} of the gcloud sdk. We recommend using at least version {MIN_GCLOUD_SDK_VERSION}.\n '
                                f'Please update your sdk version by running: gcloud components update.\n')
        except subprocess.CalledProcessError:
            logging.warning('WARNING: You do not have gcloud installed. Please install the gcloud sdk.\n')

        try:
            gcloud_beta_version = subprocess.check_output(
                ['gcloud info --format="value(installation.components.beta)" 2> /dev/null'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
            if version.parse(MIN_GCLOUD_BETA_VERSION) > version.parse(gcloud_beta_version):
                logging.warning(f'WARNING: You are currently using version {gcloud_beta_version} of the gcloud beta. We recommend using at least version {MIN_GCLOUD_BETA_VERSION}.\n '
                                f'Please update your beta version by running: gcloud components install beta.\n')
        except subprocess.CalledProcessError:
            logging.warning('WARNING: You do not have gcloud beta installed. Please install the gcloud beta by running: gcloud components install beta\n')

    if provisioning_framework == Provisioner.TERRAFORM.value:
        try:
            terraform_version_json_string = subprocess.check_output(
                ['terraform version -json 2> /dev/null'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
            terraform_version = json.loads(terraform_version_json_string)['terraform_version']
            if version.parse(MIN_RECOMMENDED_TERRAFORM_VERSION) > version.parse(terraform_version):
                logging.warning(f'WARNING: You are currently using version {terraform_version} of terraform. AutoMLOps has been tested with version {MIN_RECOMMENDED_TERRAFORM_VERSION}.\n '
                                f'We recommend updating your terraform version.\n')
        except subprocess.CalledProcessError:
            logging.warning('WARNING: You do not have terraform installed. Please install terraform.\n')

    # check for pulumi versions


def precheck_deployment_requirements(defaults: dict):
    """Checks to see if the necessary MLOps infra exists to run the deploy() step based on the user
    tooling selection determined during the generate() step.

    Args:
        defaults: Contents of the Defaults yaml file (config/defaults.yaml).
    """
    use_ci = defaults['tooling']['use_ci']
    artifact_repo_location = defaults['gcp']['artifact_repo_location']
    artifact_repo_name = defaults['gcp']['artifact_repo_name']
    artifact_repo_type = defaults['gcp']['artifact_repo_type']
    storage_bucket_name = defaults['gcp']['storage_bucket_name']
    pipeline_job_runner_service_account = defaults['gcp']['pipeline_job_runner_service_account']
    if use_ci:
        pubsub_topic_name = defaults['gcp']['pubsub_topic_name']
        pipeline_job_submission_service_name = defaults['gcp']['pipeline_job_submission_service_name']
        pipeline_job_submission_service_location = defaults['gcp']['pipeline_job_submission_service_location']
        pipeline_job_submission_service_type = defaults['gcp']['pipeline_job_submission_service_type']
        submission_svc_prefix = 'gcr' if pipeline_job_submission_service_type == PipelineJobSubmitter.CLOUD_RUN.value else 'gcf'
        pubsub_subscription_name = f'''{submission_svc_prefix}-{pipeline_job_submission_service_name}-{pipeline_job_submission_service_location}-{pubsub_topic_name}'''
        source_repository_name = defaults['gcp']['source_repository_name']
        source_repository_type = defaults['gcp']['source_repository_type']
        build_trigger_name = defaults['gcp']['build_trigger_name']
        build_trigger_location = defaults['gcp']['build_trigger_location']
        deployment_framework = defaults['tooling']['deployment_framework']

    credentials, project = google.auth.default()
    logging.info(f'Checking for required API services in project {project}...')
    service = discovery.build('serviceusage', 'v1', credentials=credentials, cache_discovery=False)
    for api in get_required_apis(defaults):
        request = service.services().get(name=f'projects/{project}/services/{api}')
        try:
            response = request.execute()
            if response['state'] != 'ENABLED':
                raise RuntimeError(f'{api} must be enabled in order to use AutoMLOps. '
                                    'Please enable this API and re-run.')
        except Exception as err:
            raise RuntimeError(f'An error was encountered: {err}') from err

    if artifact_repo_type == ArtifactRepository.ARTIFACT_REGISTRY.value:
        logging.info(f'Checking for Artifact Registry in project {project}...')
        service = discovery.build('artifactregistry', 'v1', credentials=credentials, cache_discovery=False)
        request = service.projects().locations().repositories().get(
            name=f'projects/{project}/locations/{artifact_repo_location}/repositories/{artifact_repo_name}')
        try:
            request.execute()
        except Exception as err:
            raise RuntimeError(f'Artifact Registry {artifact_repo_name} not found in project {project}. '
                                'Please create registry and continue.') from err

    logging.info(f'Checking for Storage Bucket in project {project}...')
    service = discovery.build('storage', 'v1', credentials=credentials, cache_discovery=False)
    request = service.buckets().get(bucket=storage_bucket_name)
    try:
        request.execute()
    except Exception as err:
        raise RuntimeError(f'Storage Bucket {storage_bucket_name} not found in project {project}. '
                            'Please create bucket and continue.') from err

    logging.info(f'Checking for Pipeline Runner Service Account in project {project}...')
    service = discovery.build('iam', 'v1', credentials=credentials, cache_discovery=False)
    request = service.projects().serviceAccounts().get(
        name=f'projects/{project}/serviceAccounts/{pipeline_job_runner_service_account}')
    try:
        request.execute()
    except Exception as err:
        raise RuntimeError(f'Service Account {pipeline_job_runner_service_account} not found in project {project}. '
                            'Please create service account and continue.') from err

    logging.info(f'Checking for IAM roles on Pipeline Runner Service Account in project {project}...')
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials, cache_discovery=False)
    request = service.projects().getIamPolicy(
        resource=project, body={'options': {'requestedPolicyVersion': 3}})
    try:
        response = request.execute()
        iam_roles = set()
        for element in response['bindings']:
            if f'serviceAccount:{pipeline_job_runner_service_account}' in element['members']:
                iam_roles.add(element['role'])
        if not set(IAM_ROLES_RUNNER_SA).issubset(iam_roles):
            raise RuntimeError('Missing the following IAM roles for service account '
                              f'{pipeline_job_runner_service_account}: {set(IAM_ROLES_RUNNER_SA).difference(iam_roles)}. '
                               'Please update service account roles and continue.')
    except Exception as err:
        raise RuntimeError(f'An error was encountered: {err}') from err

    if use_ci:
        if source_repository_type == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            logging.info(f'Checking for Cloud Source Repo in project {project}...')
            service = discovery.build('sourcerepo', 'v1', credentials=credentials, cache_discovery=False)
            request = service.projects().repos().get(
                name=f'projects/{project}/repos/{source_repository_name}')
            try:
                request.execute()
            except Exception as err:
                raise RuntimeError(f'Cloud Source Repo {source_repository_name} not found in project {project}. '
                                    'Please create source repo and continue.') from err

        logging.info(f'Checking for Pub/Sub Topic in project {project}...')
        service = discovery.build('pubsub', 'v1', credentials=credentials, cache_discovery=False)
        request = service.projects().topics().get(
            topic=f'projects/{project}/topics/{pubsub_topic_name}')
        try:
            request.execute()
        except Exception as err:
            raise RuntimeError(f'Pub/Sub Topic {pubsub_topic_name} not found in project {project}. '
                                'Please create Pub/Sub Topic and continue.') from err

        logging.info(f'Checking for Pub/Sub Subscription in project {project}...')
        service = discovery.build('pubsub', 'v1', credentials=credentials, cache_discovery=False)
        request = service.projects().subscriptions().get(
            subscription=f'projects/{project}/subscriptions/{pubsub_subscription_name}')
        try:
            request.execute()
        except Exception as err:
            raise RuntimeError(f'Pub/Sub Subscription {pubsub_subscription_name} not found in project {project}. '
                                'Please create Pub/Sub Subscription and continue.') from err

        if pipeline_job_submission_service_type == PipelineJobSubmitter.CLOUD_RUN.value:
            logging.info(f'Checking for Cloud Run Pipeline Job Submission Service in project {project}...')
            service = discovery.build('run', 'v1', credentials=credentials, cache_discovery=False)
            request = service.projects().locations().services().get(
                name=f'projects/{project}/locations/{pipeline_job_submission_service_location}/services/{pipeline_job_submission_service_name}')
            try:
                request.execute()
            except Exception as err:
                raise RuntimeError(f'Cloud Run Pipeline Job Submission Service {pipeline_job_submission_service_name} not found in project {project}. '
                                    'Please redeploy the submission service and continue.') from err

        if pipeline_job_submission_service_type == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            logging.info(f'Checking for Cloud Functions Pipeline Job Submission Service in project {project}...')
            service = discovery.build('cloudfunctions', 'v1', credentials=credentials, cache_discovery=False)
            request = service.projects().locations().functions().get(name=f'projects/{project}/locations/{pipeline_job_submission_service_location}/functions/{pipeline_job_submission_service_name}')
            try:
                request.execute()
            except Exception as err:
                raise RuntimeError(f'Cloud Functions Pipeline Job Submission Service {pipeline_job_submission_service_name} not found in project {project}. '
                                    'Please redeploy the submission service and continue.') from err         

        if deployment_framework == Deployer.CLOUDBUILD.value:
            logging.info(f'Checking for Cloud Build Trigger in project {project}...')
            service = discovery.build('cloudbuild', 'v1', credentials=credentials, cache_discovery=False)
            request = service.projects().locations().triggers().get(
                name=f'projects/{project}/locations/{build_trigger_location}/triggers/{build_trigger_name}',
                projectId=project, triggerId=build_trigger_name)
            try:
                request.execute()
            except Exception as err:
                raise RuntimeError(f'Cloud Build Trigger {build_trigger_name} not found in project {project}. '
                                    'Please create Cloud Build Trigger and continue.') from err

    logging.info('Precheck successfully completed, continuing to deployment.\n')


def resources_generation_manifest(defaults: dict):
    """Logs urls of generated resources.

    Args:
        defaults (dict): Contents of the Defaults yaml file (config/defaults.yaml).
    """
    logging.info('Please wait for this build job to complete.')
    logging.info('\n'
                 '#################################################################\n'
                 '#                                                               #\n'
                 '#                       RESOURCES MANIFEST                      #\n'
                 '#---------------------------------------------------------------#\n'
                 '#     Generated resources can be found at the following urls    #\n'
                 '#                                                               #\n'
                 '#################################################################\n')
    # pylint: disable=logging-fstring-interpolation
    logging.info(
        f'''Google Cloud Storage Bucket: https://console.cloud.google.com/storage/{defaults['gcp']['storage_bucket_name']}''')
    if defaults['gcp']['artifact_repo_type'] == ArtifactRepository.ARTIFACT_REGISTRY.value:
        logging.info(
            f'''Artifact Registry: https://console.cloud.google.com/artifacts/docker/{defaults['gcp']['project_id']}/{defaults['gcp']['artifact_repo_location']}/{defaults['gcp']['artifact_repo_name']}''')
    logging.info(
        f'''Service Accounts: https://console.cloud.google.com/iam-admin/serviceaccounts?project={defaults['gcp']['project_id']}''')
    logging.info('APIs: https://console.cloud.google.com/apis')
    if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
        logging.info(
            f'''Cloud Build Jobs: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['build_trigger_location']}''')
    if defaults['tooling']['orchestration_framework'] == Orchestrator.KFP.value:
        logging.info(
            'Vertex AI Pipeline Runs: https://console.cloud.google.com/vertex-ai/pipelines/runs')
    if defaults['tooling']['use_ci']:
        if defaults['gcp']['source_repository_type'] == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            logging.info(
                f'''Cloud Source Repository: https://source.cloud.google.com/{defaults['gcp']['project_id']}/{defaults['gcp']['source_repository_name']}/+/{defaults['gcp']['source_repository_branch']}:''')
        if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
            logging.info(
                f'''Cloud Build Trigger: https://console.cloud.google.com/cloud-build/triggers;region={defaults['gcp']['build_trigger_location']}''')
        if defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_RUN.value:
            logging.info(
                f'''Pipeline Job Submission Service (Cloud Run): https://console.cloud.google.com/run/detail/{defaults['gcp']['pipeline_job_submission_service_location']}/{defaults['gcp']['pipeline_job_submission_service_name']}''')
        elif defaults['gcp']['pipeline_job_submission_service_type'] == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
            logging.info(
                f'''Pipeline Job Submission Service (Cloud Functions): https://console.cloud.google.com/functions/details/{defaults['gcp']['pipeline_job_submission_service_location']}/{defaults['gcp']['pipeline_job_submission_service_name']}''')
        logging.info(
            f'''Pub/Sub Queueing Service Topic: https://console.cloud.google.com/cloudpubsub/topic/detail/{defaults['gcp']['pubsub_topic_name']}''')
        logging.info('Pub/Sub Queueing Service Subscriptions: https://console.cloud.google.com/cloudpubsub/subscription/list')
        if defaults['gcp']['schedule_pattern'] != DEFAULT_SCHEDULE_PATTERN:
            logging.info(
                'Cloud Scheduler Job: https://console.cloud.google.com/cloudscheduler')

def render_jinja(template_path, **template_vars):
    """Renders a Jinja2 template with provided variables.

    Args:
        template_path (str): The path to the Jinja2 template file.
        **template_vars: Keyword arguments representing variables to substitute in the template.

    Returns:
        str: The rendered template as a string.
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(**template_vars)

def coalesce(*arg):
    """Creates the first non-None value from a sequence of arguments.

    Returns:
        The first non-None argument, or None if all arguments are None.
    """
    for el in arg:
        if el is not None:
            return el
    return None
