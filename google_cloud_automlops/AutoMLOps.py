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

"""AutoMLOps is a tool that generates a production-style MLOps pipeline
   from Jupyter Notebooks."""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import
# pylint: disable=logging-fstring-interpolation
# pylint: disable=global-at-module-level

import functools
import json
import logging
import os
import sys
import subprocess
from typing import Callable, Dict, List, Optional

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    DEFAULT_BASE_IMAGE,
    DEFAULT_NAMING_PREFIX,
    DEFAULT_RESOURCE_LOCATION,
    DEFAULT_SCHEDULE_PATTERN,
    DEFAULT_SOURCE_REPO_BRANCH,
    DEFAULT_VPC_CONNECTOR,
    DEFAULTS_HEADER,
    GENERATED_CLOUDBUILD_FILE,
    GENERATED_GITHUB_ACTIONS_FILE,
    GENERATED_DEFAULTS_FILE,
    GENERATED_DIRS,
    GENERATED_GITHUB_DIRS,
    GENERATED_MODEL_MONITORING_DIRS,
    GENERATED_RESOURCES_SH_FILE,
    GENERATED_SERVICES_DIRS,
    GENERATED_TERRAFORM_DIRS,
    OUTPUT_DIR
)
from google_cloud_automlops.utils.utils import (
    account_permissions_warning,
    check_installation_versions,
    coalesce,
    create_default_config,
    execute_process,
    make_dirs,
    precheck_deployment_requirements,
    read_yaml_file,
    resources_generation_manifest,
    stringify_job_spec_list,
    validate_use_ci,
    write_file,
    write_yaml_file
)
# Orchestration imports
from google_cloud_automlops.utils.enums import (
    Orchestrator,
    PipelineJobSubmitter,
    Provisioner
)
from google_cloud_automlops.orchestration.base import BaseComponent, BasePipeline, BaseServices
from google_cloud_automlops.orchestration.kfp import KFPComponent, KFPPipeline, KFPServices

# Provisioning imports
from google_cloud_automlops.provisioning.base import Infrastructure
from google_cloud_automlops.provisioning.terraform import Terraform
from google_cloud_automlops.provisioning.gcloud import GCloud
from google_cloud_automlops.provisioning.pulumi import Pulumi

# Deployment imports
from google_cloud_automlops.deployments.cloudbuild import builder as CloudBuildBuilder
from google_cloud_automlops.deployments.github_actions import builder as GithubActionsBuilder
from google_cloud_automlops.deployments.enums import (
    ArtifactRepository,
    CodeRepository,
    Deployer
)
from google_cloud_automlops.deployments.configs import (
    CloudBuildConfig,
    GitHubActionsConfig
)
from google_cloud_automlops.deployments.gitops.git_utils import git_workflow

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(message)s')
logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logger = logging.getLogger()

# Create output directory
make_dirs([OUTPUT_DIR])

# Set up global dictionaries to hold pipeline and components
global components_dict
components_dict = {}

def launchAll(
    project_id: str,
    pipeline_params: Dict,
    artifact_repo_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    artifact_repo_name: Optional[str] = None,
    artifact_repo_type: Optional[str] = ArtifactRepository.ARTIFACT_REGISTRY.value,
    base_image: Optional[str] = DEFAULT_BASE_IMAGE,
    build_trigger_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    build_trigger_name: Optional[str] = None,
    custom_training_job_specs: Optional[List[Dict]] = None,
    deployment_framework: Optional[str] = Deployer.CLOUDBUILD.value,
    naming_prefix: Optional[str] = DEFAULT_NAMING_PREFIX,
    orchestration_framework: Optional[str] = Orchestrator.KFP.value,
    pipeline_job_runner_service_account: Optional[str] = None,
    pipeline_job_submission_service_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    pipeline_job_submission_service_name: Optional[str] = None,
    pipeline_job_submission_service_type: Optional[str] = PipelineJobSubmitter.CLOUD_FUNCTIONS.value,
    precheck: Optional[bool] = True,
    project_number: Optional[str] = None,
    provision_credentials_key: str = None,
    provisioning_framework: Optional[str] = Provisioner.GCLOUD.value,
    pubsub_topic_name: Optional[str] = None,
    schedule_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    schedule_name: Optional[str] = None,
    schedule_pattern: Optional[str] = DEFAULT_SCHEDULE_PATTERN,
    setup_model_monitoring: Optional[bool] = False,
    source_repo_branch: Optional[str] = DEFAULT_SOURCE_REPO_BRANCH,
    source_repo_name: Optional[str] = None,
    source_repo_type: Optional[str] = CodeRepository.CLOUD_SOURCE_REPOSITORIES.value,
    storage_bucket_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    storage_bucket_name: Optional[str] = None,
    hide_warnings: Optional[bool] = True,
    use_ci: Optional[bool] = False,
    vpc_connector: Optional[str] = DEFAULT_VPC_CONNECTOR,
    workload_identity_pool: Optional[str] = None,
    workload_identity_provider: Optional[str] = None,
    workload_identity_service_account: Optional[str] = None):
    """Generates relevant pipeline and component artifacts,
       then provisions resources, builds, compiles, and submits the PipelineJob.
       Check constants file for variable default values.

    Args:
        project_id: The project ID.
        pipeline_params: Dictionary containing runtime pipeline parameters.
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        base_image: The image to use in the component base dockerfile.
        build_trigger_location: The location of the build trigger (for cloud build).
        build_trigger_name: The name of the build trigger (for cloud build).
        custom_training_job_specs: Specifies the specs to run the training job with.
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        orchestration_framework: The orchestration framework to use (e.g. kfp, tfx, etc.)
        pipeline_job_runner_service_account: Service Account to run PipelineJobs (specify the full string).
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        precheck: Boolean used to specify whether to check for provisioned resources before deploying.
        project_number: The project number.
        provision_credentials_key: Either a path to or the contents of a service account key file in JSON format.
        provisioning_framework: The IaC tool to use (e.g. Terraform, Pulumi, etc.)
        pubsub_topic_name: The name of the pubsub topic to publish to.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        setup_model_monitoring: Boolean parameter which specifies whether to set up a Vertex AI Model Monitoring Job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        hide_warnings: Boolean used to specify whether to show provision/deploy permission warnings
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
        workload_identity_pool: Pool for workload identity federation. 
        workload_identity_provider: Provider for workload identity federation.
        workload_identity_service_account: Service account for workload identity federation (specify the full string).
    """
    generate(
        project_id=project_id,
        pipeline_params=pipeline_params,
        artifact_repo_location=artifact_repo_location,
        artifact_repo_name=artifact_repo_name,
        artifact_repo_type=artifact_repo_type,
        base_image=base_image,
        build_trigger_location=build_trigger_location,
        build_trigger_name=build_trigger_name,
        custom_training_job_specs=custom_training_job_specs,
        deployment_framework=deployment_framework,
        naming_prefix=naming_prefix,
        orchestration_framework=orchestration_framework,
        pipeline_job_runner_service_account=pipeline_job_runner_service_account,
        pipeline_job_submission_service_location=pipeline_job_submission_service_location,
        pipeline_job_submission_service_name=pipeline_job_submission_service_name,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        project_number=project_number,
        provisioning_framework=provisioning_framework,
        provision_credentials_key=provision_credentials_key,
        pubsub_topic_name=pubsub_topic_name,
        schedule_location=schedule_location,
        schedule_name=schedule_name,
        schedule_pattern=schedule_pattern,
        setup_model_monitoring=setup_model_monitoring,
        source_repo_branch=source_repo_branch,
        source_repo_name=source_repo_name,
        source_repo_type=source_repo_type,
        storage_bucket_location=storage_bucket_location,
        storage_bucket_name=storage_bucket_name,
        use_ci=use_ci,
        vpc_connector=vpc_connector,
        workload_identity_pool=workload_identity_pool,
        workload_identity_provider=workload_identity_provider,
        workload_identity_service_account=workload_identity_service_account)
    provision(hide_warnings=hide_warnings)
    deploy(hide_warnings=hide_warnings, precheck=precheck)


def generate(
    project_id: str,
    pipeline_params: Dict,
    artifact_repo_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    artifact_repo_name: Optional[str] = None,
    artifact_repo_type: Optional[str] = ArtifactRepository.ARTIFACT_REGISTRY.value,
    base_image: Optional[str] = DEFAULT_BASE_IMAGE,
    build_trigger_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    build_trigger_name: Optional[str] = None,
    custom_training_job_specs: Optional[List[Dict]] = None,
    deployment_framework: Optional[str] = Deployer.CLOUDBUILD.value,
    naming_prefix: Optional[str] = DEFAULT_NAMING_PREFIX,
    orchestration_framework: Optional[str] = Orchestrator.KFP.value,
    pipeline_job_runner_service_account: Optional[str] = None,
    pipeline_job_submission_service_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    pipeline_job_submission_service_name: Optional[str] = None,
    pipeline_job_submission_service_type: Optional[str] = PipelineJobSubmitter.CLOUD_FUNCTIONS.value,
    project_number: Optional[str] = None,
    provision_credentials_key: str = None,
    provisioning_framework: Optional[str] = Provisioner.GCLOUD.value,
    pubsub_topic_name: Optional[str] = None,
    schedule_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    schedule_name: Optional[str] = None,
    schedule_pattern: Optional[str] = DEFAULT_SCHEDULE_PATTERN,
    setup_model_monitoring: Optional[bool] = False,
    source_repo_branch: Optional[str] = DEFAULT_SOURCE_REPO_BRANCH,
    source_repo_name: Optional[str] = None,
    source_repo_type: Optional[str] = CodeRepository.CLOUD_SOURCE_REPOSITORIES.value,
    storage_bucket_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    storage_bucket_name: Optional[str] = None,
    use_ci: Optional[bool] = False,
    vpc_connector: Optional[str] = DEFAULT_VPC_CONNECTOR,
    workload_identity_pool: Optional[str] = None, #TODO: integrate optional creation of pool and provider during provisioning stage
    workload_identity_provider: Optional[str] = None,
    workload_identity_service_account: Optional[str] = None):
    """Generates relevant pipeline and component artifacts.
       Check constants file for variable default values.

    Args: See launchAll() function.
    """
    # Validate that use_ci=True if schedule_pattern parameter is set or setup_model_monitoring is True
    validate_use_ci(setup_model_monitoring, schedule_pattern, use_ci)

    # Validate currently supported tools
    if artifact_repo_type not in [e.value for e in ArtifactRepository]:
        raise ValueError(f'Unsupported artifact repository type: {artifact_repo_type}')
    if source_repo_type not in [e.value for e in CodeRepository]:
        raise ValueError(f'Unsupported source repository type: {source_repo_type}')
    if pipeline_job_submission_service_type not in [e.value for e in PipelineJobSubmitter]:
        raise ValueError(f'Unsupported pipeline job submissions service type: {pipeline_job_submission_service_type}')
    if orchestration_framework not in [e.value for e in Orchestrator]:
        raise ValueError(f'Unsupported orchestration framework: {orchestration_framework}')
    if provisioning_framework not in [e.value for e in Provisioner]:
        raise ValueError(f'Unsupported provisioning framework: {provisioning_framework}')
    if deployment_framework not in [e.value for e in Deployer]:
        raise ValueError(f'Unsupported deployment framework: {deployment_framework}')

    logging.info(f'Writing directories under {BASE_DIR}')

    # Make standard directories
    make_dirs(GENERATED_DIRS)

    # Make optional directories
    if use_ci:
        make_dirs(GENERATED_SERVICES_DIRS)
    if provisioning_framework == Provisioner.TERRAFORM.value:
        make_dirs(GENERATED_TERRAFORM_DIRS)
    if deployment_framework == Deployer.GITHUB_ACTIONS.value:
        make_dirs(GENERATED_GITHUB_DIRS)
    if setup_model_monitoring:
        make_dirs(GENERATED_MODEL_MONITORING_DIRS)

    # Set derived vars if none were given for certain variables
    derived_artifact_repo_name = coalesce(artifact_repo_name, f'{naming_prefix}-artifact-registry')
    derived_build_trigger_name = coalesce(build_trigger_name, f'{naming_prefix}-build-trigger')
    derived_custom_training_job_specs = stringify_job_spec_list(custom_training_job_specs)
    derived_pipeline_job_runner_service_account = coalesce(pipeline_job_runner_service_account, f'vertex-pipelines@{project_id}.iam.gserviceaccount.com')
    derived_pipeline_job_submission_service_name = coalesce(pipeline_job_submission_service_name, f'{naming_prefix}-job-submission-svc')
    derived_pubsub_topic_name = coalesce(pubsub_topic_name, f'{naming_prefix}-queueing-svc')
    derived_schedule_name = coalesce(schedule_name, f'{naming_prefix}-schedule')
    derived_source_repo_name = coalesce(source_repo_name, f'{naming_prefix}-repository')
    derived_storage_bucket_name = coalesce(storage_bucket_name, f'{project_id}-{naming_prefix}-bucket')

    # Write defaults.yaml
    defaults = create_default_config(
        artifact_repo_location=artifact_repo_location,
        artifact_repo_name=derived_artifact_repo_name,
        artifact_repo_type=artifact_repo_type,
        base_image=base_image,
        build_trigger_location=build_trigger_location,
        build_trigger_name=derived_build_trigger_name,
        deployment_framework=deployment_framework,
        naming_prefix=naming_prefix,
        orchestration_framework=orchestration_framework,
        pipeline_job_runner_service_account=derived_pipeline_job_runner_service_account,
        pipeline_job_submission_service_location=pipeline_job_submission_service_location,
        pipeline_job_submission_service_name=derived_pipeline_job_submission_service_name,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        project_id=project_id,
        provisioning_framework=provisioning_framework,
        pubsub_topic_name=derived_pubsub_topic_name,
        schedule_location=schedule_location,
        schedule_name=derived_schedule_name,
        schedule_pattern=schedule_pattern,
        setup_model_monitoring=setup_model_monitoring,
        source_repo_branch=source_repo_branch,
        source_repo_name=derived_source_repo_name,
        source_repo_type=source_repo_type,
        storage_bucket_location=storage_bucket_location,
        storage_bucket_name=derived_storage_bucket_name,
        use_ci=use_ci,
        vpc_connector=vpc_connector)
    logging.info(f'Writing configurations to {GENERATED_DEFAULTS_FILE}')
    # Write header and then yaml contents
    write_file(GENERATED_DEFAULTS_FILE, DEFAULTS_HEADER, 'w')
    write_yaml_file(GENERATED_DEFAULTS_FILE, defaults, 'a')

    # Generate files required to run a Kubeflow pipeline
    if orchestration_framework == Orchestrator.KFP.value:

        # Log what files will be created
        logging.info(f'Writing README.md to {BASE_DIR}README.md')
        logging.info(f'Writing scripts to {BASE_DIR}scripts')

        # Write kubeflow pipeline code
        logging.info(f'Writing kubeflow pipelines code to {BASE_DIR}pipelines')
        kfppipe = KFPPipeline(func=pipeline_glob.func,
                              name=pipeline_glob.name,
                              description=pipeline_glob.description,
                              comps_dict=components_dict)
        kfppipe.build(pipeline_params, derived_custom_training_job_specs)

        # Write kubeflow components code
        logging.info(f'Writing kubeflow components code to {BASE_DIR}components')
        for comp in kfppipe.comps:
            logging.info(f'     -- Writing {comp.name}')
            KFPComponent(func=comp.func, packages_to_install=comp.packages_to_install).build()

        if setup_model_monitoring:
            logging.info(f'Writing model monitoring code to {BASE_DIR}model_monitoring')

        # If user specified services, write services scripts
        if use_ci:
            logging.info(f'Writing submission service code to {BASE_DIR}services')
            defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
            KFPServices().build()

    # Generate files required to provision resources
    if provisioning_framework == Provisioner.GCLOUD.value:
        logging.info(f'Writing gcloud provisioning code to {BASE_DIR}provision')
        GCloud(provision_credentials_key=provision_credentials_key).build()

    elif provisioning_framework == Provisioner.TERRAFORM.value:
        logging.info(f'Writing terraform provisioning code to {BASE_DIR}provision')
        Terraform(provision_credentials_key=provision_credentials_key).build()

    # Pulumi - Currently a roadmap item
    # elif provisioning_framework == Provisioner.PULUMI.value:
    #     Pulumi(provision_credentials_key=provision_credentials_key).build()

    # Generate files required to run cicd pipeline
    if deployment_framework == Deployer.CLOUDBUILD.value:
        logging.info(f'Writing cloud build config to {GENERATED_CLOUDBUILD_FILE}')
        CloudBuildBuilder.build(CloudBuildConfig(
                artifact_repo_location=artifact_repo_location,
                artifact_repo_name=derived_artifact_repo_name,
                naming_prefix=naming_prefix,
                project_id=project_id,
                pubsub_topic_name=derived_pubsub_topic_name,
                use_ci=use_ci))
    if deployment_framework == Deployer.GITHUB_ACTIONS.value:
        if project_number is None:
            raise ValueError('Project number must be specified in order to use to use Github Actions integration.')
        logging.info(f'Writing GitHub Actions config to {GENERATED_GITHUB_ACTIONS_FILE}')
        GithubActionsBuilder.build(GitHubActionsConfig(
                artifact_repo_location=artifact_repo_location,
                artifact_repo_name=derived_artifact_repo_name,
                naming_prefix=naming_prefix,
                project_id=project_id,
                project_number=project_number,
                pubsub_topic_name=derived_pubsub_topic_name,
                source_repo_branch=source_repo_branch,
                use_ci=use_ci,
                workload_identity_pool=workload_identity_pool,
                workload_identity_provider=workload_identity_provider,
                workload_identity_service_account=workload_identity_service_account))
    logging.info('Code Generation Complete.')


def provision(hide_warnings: Optional[bool] = True):
    """Provisions the necessary infra to run MLOps pipelines. 
       The provisioning option (e.g. terraform, gcloud, etc.)
       is set during the generate() step and stored in config/defaults.yaml. 

    Args:
        hide_warnings: Boolean that specifies whether to show permissions warnings before provisioning.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    provisioning_framework = defaults['tooling']['provisioning_framework']

    if not hide_warnings:
        check_installation_versions(provisioning_framework=provisioning_framework)
        account_permissions_warning(operation='provision', defaults=defaults)

    if provisioning_framework == Provisioner.GCLOUD.value:
        execute_process(f'./{GENERATED_RESOURCES_SH_FILE}', to_null=False)
    elif provisioning_framework == Provisioner.TERRAFORM.value:
        execute_process(f'./{GENERATED_RESOURCES_SH_FILE} state_bucket', to_null=False)
        execute_process(f'./{GENERATED_RESOURCES_SH_FILE} environment', to_null=False)


def deprovision():
    """De-provisions the infra stood up during the provision() step.
       deprovision currently only works with terraform. 
       The provisioning option (e.g. terraform, gcloud, etc.)
       is set during the generate() step and stored in config/defaults.yaml. 
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    provisioning_framework = defaults['tooling']['provisioning_framework']

    if provisioning_framework == Provisioner.GCLOUD.value:
        raise ValueError('De-provisioning is currently only supported for provisioning_framework={terraform, pulumi}.')

    execute_process(f'terraform -chdir={BASE_DIR}provision/environment destroy -auto-approve', to_null=False)


def deploy(
    hide_warnings: Optional[bool] = True,
    precheck: Optional[bool] = False):

    """Builds and pushes the component_base image, compiles the pipeline,
       and submits a message to the queueing service to execute a PipelineJob.
       The specifics of the deploy step are dependent on the defaults set during
       the generate() step, particularly:
       - use_ci: if use_ci is False, the deploy step will use scripts/run_all.sh,
            which will submit the build job, compile the pipeline, and submit the
            PipelineJob all from the local machine.
       - artifact_repo_type: Determines which type of artifact repo the image
            is pushed to.
       - deployment_framework: Determines which build tool to use for building.
       - source_repo_type: Determines which source repo to use for versioning code
            and triggering the build.
       Defaults are stored in config/defaults.yaml.

    Args:
        hide_warnings: Boolean that specifies whether to show permissions warnings before deploying.
        precheck: Boolean that specifies whether to check if the infra exists before deploying.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    use_ci = defaults['tooling']['use_ci']

    if precheck:
        if not hide_warnings:
            account_permissions_warning(operation='deploy_with_precheck', defaults=defaults)
        precheck_deployment_requirements(defaults)
    else:
        if not hide_warnings:
            account_permissions_warning(operation='deploy_without_precheck', defaults=defaults)

    # Build, compile, and submit pipeline job
    if use_ci:
        git_workflow()
    else:
        os.chdir(BASE_DIR)
        try:
            subprocess.run(['./scripts/run_all.sh'], shell=True,
                           check=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.info(e) # graceful error exit to allow for cd-ing back
        os.chdir('../')

    # Log generated resources
    resources_generation_manifest(defaults)

def monitor(
    target_field: str,
    model_endpoint: str,
    alert_emails: Optional[list] = None,
    auto_retraining_params: Optional[dict] = None,
    drift_thresholds: Optional[dict] = None,
    hide_warnings: Optional[bool] = True,
    job_display_name: Optional[str] = None,
    monitoring_interval: Optional[int] = 1,
    monitoring_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    sample_rate: Optional[float] = 0.8,
    skew_thresholds: Optional[dict] = None,
    training_dataset: Optional[str] = None):
    """Creates or updates a Vertex AI Model Monitoring Job for a deployed model endpoint.
       - The predicted target field and model endpoint are required.
       - alert_emails, if specified, will send monitoring updates to the specified email(s)
       - auto_retraining_params will set up automatic retraining by creating a Log Sink and
            forwarding anomaly logs to the Pub/Sub Topic for retraining the model with the
            params specified here. If this field is left Null, the model will not be
            automatically retrained when an anomaly is detected.
       - drift_thresholds and skew_thresholds are optional, but at least 1 of them 
            must be specified.
       - training_dataset must be specified if skew_thresholds are provided.
       Defaults are stored in config/defaults.yaml.

    Args:
        target_field: Prediction target column name in training dataset.
        model_endpoint: Endpoint resource name of the deployed model to monitoring.
            Format: projects/{project}/locations/{location}/endpoints/{endpoint}
        alert_emails: Optional list of emails to send monitoring alerts.
            Email alerts not used if this value is set to None.
        auto_retraining_params: Pipeline parameter values to use when retraining the model.
            Defaults to None; if left None, the model will not be retrained if an alert is generated.
        drift_thresholds: Compares incoming data to data previously seen to check for drift.
        hide_warnings: Boolean that specifies whether to show permissions warnings before monitoring.
        job_display_name: Display name of the ModelDeploymentMonitoringJob. The name can be up to 128 characters 
            long and can be consist of any UTF-8 characters.
        monitoring_interval: Configures model monitoring job scheduling interval in hours.
            This defines how often the monitoring jobs are triggered.
        monitoring_location: Location to retrieve ModelDeploymentMonitoringJob from.
        sample_rate: Used for drift detection, specifies what percent of requests to the endpoint are randomly sampled
            for drift detection analysis. This value most range between (0, 1].
        skew_thresholds: Compares incoming data to the training dataset to check for skew.
        training_dataset: Training dataset used to train the deployed model. This field is required if
            using skew detection.
    """
    if not skew_thresholds and not drift_thresholds:
        raise ValueError('skew_thresolds and drift_thresholds cannot both be None.')
    elif skew_thresholds and not training_dataset:
        raise ValueError('training_dataset must be set to use skew_thresolds.')

    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    if not defaults['gcp']['setup_model_monitoring']:
        raise ValueError('Parameter setup_model_monitoring in .generate() must be set to True to use .monitor()')
    if not hide_warnings:
        account_permissions_warning(operation='model_monitoring', defaults=defaults)

    derived_job_display_name = f'''{defaults['gcp']['naming_prefix']}-model-monitoring-job''' if job_display_name is None else job_display_name
    derived_log_sink_name = f'''{defaults['gcp']['naming_prefix']}-model-monitoring-log-sink'''
    defaults['monitoring']['target_field'] = target_field
    defaults['monitoring']['model_endpoint'] = model_endpoint
    defaults['monitoring']['alert_emails'] = alert_emails
    defaults['monitoring']['auto_retraining_params'] = auto_retraining_params
    defaults['monitoring']['drift_thresholds'] = drift_thresholds
    defaults['monitoring']['gs_auto_retraining_params_path'] = f'''gs://{defaults['gcp']['storage_bucket_name']}/pipeline_root/{defaults['gcp']['naming_prefix']}/automatic_retraining_parameters.json'''
    defaults['monitoring']['job_display_name'] = derived_job_display_name
    defaults['monitoring']['log_sink_name'] = derived_log_sink_name
    defaults['monitoring']['monitoring_interval'] = monitoring_interval
    defaults['monitoring']['monitoring_location'] = monitoring_location
    defaults['monitoring']['sample_rate'] = sample_rate
    defaults['monitoring']['skew_thresholds'] = skew_thresholds
    defaults['monitoring']['training_dataset'] = training_dataset

    write_file(GENERATED_DEFAULTS_FILE, DEFAULTS_HEADER, 'w')
    write_yaml_file(GENERATED_DEFAULTS_FILE, defaults, 'a')

    os.chdir(BASE_DIR)
    try:
        subprocess.run(['./scripts/create_model_monitoring_job.sh'], shell=True,
                        check=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logging.info(e) # graceful error exit to allow for cd-ing back
    os.chdir('../')


def component(func: Optional[Callable] = None,
              *,
              packages_to_install: Optional[List[str]] = None):
    """Decorator for Python-function based components in AutoMLOps.

    Example usage:
    from google_cloud_automlops import AutoMLOps
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
        components_dict[func.__name__] = BaseComponent(
            func=func,
            packages_to_install=packages_to_install
        )
        return


def pipeline(func: Optional[Callable] = None,
             *,
             name: Optional[str] = None,
             description: Optional[str] = None):
    """Decorator for Python-function based pipelines in AutoMLOps.

    Example usage:
    from google_cloud_automlops import AutoMLOps
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
        global pipeline_glob
        pipeline_glob = BasePipeline(func=func,
                                 name=name,
                                 description=description,
                                 comps_dict=components_dict)
        return


def clear_cache():
    """Deletes all temporary files stored in the cache directory."""
    execute_process(f'rm -rf {OUTPUT_DIR}', to_null=False)
    make_dirs([OUTPUT_DIR])
    logging.info('Cache cleared.')
