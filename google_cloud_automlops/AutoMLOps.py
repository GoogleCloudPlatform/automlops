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

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    DEFAULT_BASE_IMAGE,
    DEFAULT_NAMING_PREFIX,
    DEFAULT_RESOURCE_LOCATION,
    DEFAULT_SCHEDULE_PATTERN,
    DEFAULT_SOURCE_REPO_BRANCH,
    DEFAULT_VPC_CONNECTOR,
    GENERATED_CLOUDBUILD_FILE,
    GENERATED_DEFAULTS_FILE,
    GENERATED_DIRS,
    GENERATED_PROVISION_DIRS,
    GENERATED_RESOURCES_SH_FILE,
    GENERATED_SERVICES_DIRS,
    GENERATED_TERRAFORM_DIRS,
    OUTPUT_DIR
)
from google_cloud_automlops.utils.utils import (
    account_permissions_warning,
    check_installation_versions,
    create_default_config,
    execute_process,
    make_dirs,
    precheck_deployment_requirements,
    read_yaml_file,
    resources_generation_manifest,
    stringify_job_spec_list,
    validate_schedule,
    write_file
)
# Orchestration imports
from google_cloud_automlops.orchestration.kfp import builder as KfpBuilder
from google_cloud_automlops.orchestration.kfp import scaffold as KfpScaffold
from google_cloud_automlops.orchestration.enums import (
    Orchestrator,
    PipelineJobSubmitter
)
from google_cloud_automlops.orchestration.configs import (
    KfpConfig
)
# Provisioning imports
from google_cloud_automlops.provisioning.pulumi import builder as PulumiBuilder
from google_cloud_automlops.provisioning.terraform import builder as TerraformBuilder
from google_cloud_automlops.provisioning.gcloud import builder as GcloudBuilder
from google_cloud_automlops.provisioning.enums import Provisioner
from google_cloud_automlops.provisioning.configs import (
    PulumiConfig,
    TerraformConfig,
    GcloudConfig
)
# Deployment imports
from google_cloud_automlops.deployments.cloudbuild import builder as CloudBuildBuilder
from google_cloud_automlops.deployments.enums import (
    ArtifactRepository,
    CodeRepository,
    Deployer
)
from google_cloud_automlops.deployments.configs import (
    CloudBuildConfig
)
from google_cloud_automlops.deployments.gitops.git_utils import git_workflow

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(message)s')
logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logger = logging.getLogger()

make_dirs([OUTPUT_DIR])

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
    provision_credentials_key: str = None,
    provisioning_framework: Optional[str] = Provisioner.GCLOUD.value,
    pubsub_topic_name: Optional[str] = None,
    schedule_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    schedule_name: Optional[str] = None,
    schedule_pattern: Optional[str] = DEFAULT_SCHEDULE_PATTERN,
    source_repo_branch: Optional[str] = DEFAULT_SOURCE_REPO_BRANCH,
    source_repo_name: Optional[str] = None,
    source_repo_type: Optional[str] = CodeRepository.CLOUD_SOURCE_REPOSITORIES.value,
    storage_bucket_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    storage_bucket_name: Optional[str] = None,
    hide_warnings: Optional[bool] = True,
    use_ci: Optional[bool] = False,
    vpc_connector: Optional[str] = DEFAULT_VPC_CONNECTOR):
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
        pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        precheck: Boolean used to specify whether to check for provisioned resources before deploying.
        provision_credentials_key: Either a path to or the contents of a service account key file in JSON format.
        provisioning_framework: The IaC tool to use (e.g. Terraform, Pulumi, etc.)
        pubsub_topic_name: The name of the pubsub topic to publish to.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        hide_warnings: Boolean used to specify whether to show provision/deploy permission warnings
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
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
        provisioning_framework=provisioning_framework,
        provision_credentials_key=provision_credentials_key,
        pubsub_topic_name=pubsub_topic_name,
        schedule_location=schedule_location,
        schedule_name=schedule_name,
        schedule_pattern=schedule_pattern,
        source_repo_branch=source_repo_branch,
        source_repo_name=source_repo_name,
        source_repo_type=source_repo_type,
        storage_bucket_location=storage_bucket_location,
        storage_bucket_name=storage_bucket_name,
        use_ci=use_ci,
        vpc_connector=vpc_connector)
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
    provision_credentials_key: str = None,
    provisioning_framework: Optional[str] = Provisioner.GCLOUD.value,
    pubsub_topic_name: Optional[str] = None,
    schedule_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    schedule_name: Optional[str] = None,
    schedule_pattern: Optional[str] = DEFAULT_SCHEDULE_PATTERN,
    source_repo_branch: Optional[str] = DEFAULT_SOURCE_REPO_BRANCH,
    source_repo_name: Optional[str] = None,
    source_repo_type: Optional[str] = CodeRepository.CLOUD_SOURCE_REPOSITORIES.value,
    storage_bucket_location: Optional[str] = DEFAULT_RESOURCE_LOCATION,
    storage_bucket_name: Optional[str] = None,
    use_ci: Optional[bool] = False,
    vpc_connector: Optional[str] = DEFAULT_VPC_CONNECTOR):
    """Generates relevant pipeline and component artifacts.
       Check constants file for variable default values.

    Args: See launchAll() function.
    """
    # Validate that use_ci=True if schedule_pattern parameter is set
    validate_schedule(schedule_pattern, use_ci)

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
        make_dirs(GENERATED_PROVISION_DIRS)
    if provisioning_framework == Provisioner.TERRAFORM.value:
        make_dirs(GENERATED_TERRAFORM_DIRS)

    # Set derived vars if none were given for certain variables
    derived_artifact_repo_name = f'{naming_prefix}-artifact-registry' if artifact_repo_name is None else artifact_repo_name
    derived_build_trigger_name = f'{naming_prefix}-build-trigger' if build_trigger_name is None else build_trigger_name
    derived_custom_training_job_specs = stringify_job_spec_list(custom_training_job_specs) if custom_training_job_specs is not None else custom_training_job_specs
    derived_pipeline_job_runner_service_account = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com' if pipeline_job_runner_service_account is None else pipeline_job_runner_service_account
    derived_pipeline_job_submission_service_name = f'{naming_prefix}-job-submission-svc' if pipeline_job_submission_service_name is None else pipeline_job_submission_service_name
    derived_pubsub_topic_name = f'{naming_prefix}-queueing-svc' if pubsub_topic_name is None else pubsub_topic_name
    derived_schedule_name = f'{naming_prefix}-schedule' if schedule_name is None else schedule_name
    derived_source_repo_name = f'{naming_prefix}-repository' if source_repo_name is None else source_repo_name
    derived_storage_bucket_name = f'{project_id}-{naming_prefix}-bucket' if storage_bucket_name is None else storage_bucket_name

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
        source_repo_branch=source_repo_branch,
        source_repo_name=derived_source_repo_name,
        source_repo_type=source_repo_type,
        storage_bucket_location=storage_bucket_location,
        storage_bucket_name=derived_storage_bucket_name,
        use_ci=use_ci,
        vpc_connector=vpc_connector)
    logging.info(f'Writing configurations to {GENERATED_DEFAULTS_FILE}')
    write_file(GENERATED_DEFAULTS_FILE, defaults, 'w')

    # Generate files required to run a Kubeflow pipeline
    if orchestration_framework == Orchestrator.KFP.value:
        logging.info(f'Writing README.md to {BASE_DIR}README.md')
        logging.info(f'Writing kubeflow pipelines code to {BASE_DIR}pipelines, {BASE_DIR}components')
        logging.info(f'Writing scripts to {BASE_DIR}scripts')
        logging.info(f'Writing submission service code to {BASE_DIR}services')
        KfpBuilder.build(KfpConfig(
            base_image=base_image,
            custom_training_job_specs=derived_custom_training_job_specs,
            pipeline_params=pipeline_params,
            pubsub_topic_name=derived_pubsub_topic_name,
            use_ci=use_ci))

    # Generate files required to provision resources
    if provisioning_framework == Provisioner.GCLOUD.value:
        logging.info(f'Writing gcloud provisioning code to {BASE_DIR}provision')
        GcloudBuilder.build(project_id, GcloudConfig(
            artifact_repo_location=artifact_repo_location,
            artifact_repo_name=derived_artifact_repo_name,
            artifact_repo_type=artifact_repo_type,
            build_trigger_location=build_trigger_location,
            build_trigger_name=derived_build_trigger_name,
            deployment_framework=deployment_framework,
            naming_prefix=naming_prefix,
            pipeline_job_runner_service_account=derived_pipeline_job_runner_service_account,
            pipeline_job_submission_service_location=pipeline_job_submission_service_location,
            pipeline_job_submission_service_name=derived_pipeline_job_submission_service_name,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type,
            pubsub_topic_name=derived_pubsub_topic_name,
            schedule_location=schedule_location,
            schedule_name=derived_schedule_name,
            schedule_pattern=schedule_pattern,
            source_repo_branch=source_repo_branch,
            source_repo_name=derived_source_repo_name,
            source_repo_type=source_repo_type,
            storage_bucket_location=storage_bucket_location,
            storage_bucket_name=derived_storage_bucket_name,
            use_ci=use_ci,
            vpc_connector=vpc_connector))

    elif provisioning_framework == Provisioner.TERRAFORM.value:
        logging.info(f'Writing terraform provisioning code to {BASE_DIR}provision')
        TerraformBuilder.build(project_id, TerraformConfig(
            artifact_repo_location=artifact_repo_location,
            artifact_repo_name=derived_artifact_repo_name,
            artifact_repo_type=artifact_repo_type,
            build_trigger_location=build_trigger_location,
            build_trigger_name=derived_build_trigger_name,
            deployment_framework=deployment_framework,
            naming_prefix=naming_prefix,
            pipeline_job_runner_service_account=derived_pipeline_job_runner_service_account,
            pipeline_job_submission_service_location=pipeline_job_submission_service_location,
            pipeline_job_submission_service_name=derived_pipeline_job_submission_service_name,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type,
            provision_credentials_key=provision_credentials_key,
            pubsub_topic_name=derived_pubsub_topic_name,
            schedule_location=schedule_location,
            schedule_name=derived_schedule_name,
            schedule_pattern=schedule_pattern,
            source_repo_branch=source_repo_branch,
            source_repo_name=derived_source_repo_name,
            source_repo_type=source_repo_type,
            storage_bucket_location=storage_bucket_location,
            storage_bucket_name=derived_storage_bucket_name,
            use_ci=use_ci,
            vpc_connector=vpc_connector))

    # Pulumi - Currently a roadmap item
    # elif provisioning_framework == Provisioner.PULUMI.value:
    #     PulumiBuilder.build(project_id, PulumiConfig)

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
        return KfpScaffold.create_component_scaffold(
            func=func,
            packages_to_install=packages_to_install)


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
        return KfpScaffold.create_pipeline_scaffold(
            func=func,
            name=name,
            description=description)


def clear_cache():
    """Deletes all temporary files stored in the cache directory."""
    execute_process(f'rm -rf {OUTPUT_DIR}', to_null=False)
    make_dirs([OUTPUT_DIR])
    logging.info('Cache cleared.')
