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

"""Builds Terraform Files"""

# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.utils.utils import (
    get_required_apis,
    read_yaml_file,
    render_jinja,
    write_and_chmod,
    write_file
)

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_DEFAULTS_FILE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_RESOURCES_SH_FILE,
    IAM_ROLES_RUNNER_SA,
    TERRAFORM_TEMPLATES_PATH
)

from google_cloud_automlops.deployments.enums import (
    Deployer
)

from google_cloud_automlops.provisioning.configs import TerraformConfig

def build(
    project_id: str,
    config: TerraformConfig
):
    """Constructs and writes terraform scripts: Generates infrastructure using terraform hcl resource management style.

    Args:
        config.artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        config.artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        config.artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        config.build_trigger_location: The location of the build trigger (for cloud build).
        config.build_trigger_name: The name of the build trigger (for cloud build).
        config.deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        config.naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        config.pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        config.pipeline_job_submission_service_location: The location of the cloud submission service.
        config.pipeline_job_submission_service_name: The name of the cloud submission service.
        config.pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        config.provision_credentials_key: Either a path to or the contents of a service account key file in JSON format.
        config.pubsub_topic_name: The name of the pubsub topic to publish to.
        config.schedule_location: The location of the scheduler resource.
        config.schedule_name: The name of the scheduler resource.
        config.schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        config.source_repo_branch: The branch to use in the source repository.
        config.source_repo_name: The name of the source repository to use.
        config.source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        config.storage_bucket_location: Region of the GS bucket.
        config.storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        config.use_ci: Flag that determines whether to use Cloud CI/CD.
        config.vpc_connector: The name of the vpc connector to use.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    required_apis = get_required_apis(defaults)

    # create environment/data.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/data.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'data.tf.j2',
            generated_license=GENERATED_LICENSE,
            required_apis=required_apis,
            required_iam_roles=IAM_ROLES_RUNNER_SA,
            use_ci=config.use_ci
        ),
        mode='w')

    # create environment/iam.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/iam.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'iam.tf.j2',
            generated_license=GENERATED_LICENSE
        ),
        mode='w')

    # create environment/main.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/main.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'main.tf.j2',
            artifact_repo_type=config.artifact_repo_type,
            base_dir=BASE_DIR,
            deployment_framework=config.deployment_framework,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            naming_prefix=config.naming_prefix,
            pipeline_job_submission_service_type=config.pipeline_job_submission_service_type,
            schedule_pattern=config.schedule_pattern,
            source_repo_type=config.source_repo_type,
            use_ci=config.use_ci,
            vpc_connector=config.vpc_connector
        ),
        mode='w')

    # create environment/outputs.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/outputs.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'outputs.tf.j2',
            artifact_repo_type=config.artifact_repo_type,
            deployment_framework=config.deployment_framework,
            generated_license=GENERATED_LICENSE,
            pipeline_job_submission_service_type=config.pipeline_job_submission_service_type,
            schedule_pattern=config.schedule_pattern,
            source_repo_type=config.source_repo_type,
            use_ci=config.use_ci
        ),
        mode='w')

    # create environment/provider.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/provider.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'provider.tf.j2',
            generated_license=GENERATED_LICENSE
        ),
        mode='w')

    # create environment/variables.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/variables.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.tf.j2',
            generated_license=GENERATED_LICENSE
        ),
        mode='w')

    # create environment/variables.auto.tfvars
    if config.deployment_framework == Deployer.CLOUDBUILD.value:
        write_file(
            filepath=f'{BASE_DIR}provision/environment/variables.auto.tfvars',
            text=render_jinja(
                template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.auto.tfvars.j2',
                artifact_repo_location=config.artifact_repo_location,
                artifact_repo_name=config.artifact_repo_name,
                build_trigger_location=config.build_trigger_location,
                build_trigger_name=config.build_trigger_name,
                generated_license=GENERATED_LICENSE,
                pipeline_job_runner_service_account=config.pipeline_job_runner_service_account,
                pipeline_job_submission_service_location=config.pipeline_job_submission_service_location,
                pipeline_job_submission_service_name=config.pipeline_job_submission_service_name,
                project_id=project_id,
                provision_credentials_key=config.provision_credentials_key,
                pubsub_topic_name=config.pubsub_topic_name,
                schedule_location=config.schedule_location,
                schedule_name=config.schedule_name,
                schedule_pattern=config.schedule_pattern,
                source_repo_branch=config.source_repo_branch,
                source_repo_name=config.source_repo_name,
                storage_bucket_location=config.storage_bucket_location,
                storage_bucket_name=config.storage_bucket_name,
                vpc_connector=config.vpc_connector
            ),
            mode='w')

    #TODO: implement workload identity as optional
    if config.deployment_framework == Deployer.GITHUB_ACTIONS.value:
        write_file(
            filepath=f'{BASE_DIR}provision/environment/variables.auto.tfvars',
            text=render_jinja(
                template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.auto.tfvars.j2',
                artifact_repo_location=config.artifact_repo_location,
                artifact_repo_name=config.artifact_repo_name,
                build_trigger_location=config.build_trigger_location,
                build_trigger_name=config.build_trigger_name,
                generated_license=GENERATED_LICENSE,
                pipeline_job_runner_service_account=config.pipeline_job_runner_service_account,
                pipeline_job_submission_service_location=config.pipeline_job_submission_service_location,
                pipeline_job_submission_service_name=config.pipeline_job_submission_service_name,
                project_id=project_id,
                provision_credentials_key=config.provision_credentials_key,
                pubsub_topic_name=config.pubsub_topic_name,
                schedule_location=config.schedule_location,
                schedule_name=config.schedule_name,
                schedule_pattern=config.schedule_pattern,
                source_repo_branch=config.source_repo_branch,
                source_repo_name=config.source_repo_name,
                storage_bucket_location=config.storage_bucket_location,
                storage_bucket_name=config.storage_bucket_name,
                vpc_connector=config.vpc_connector
            ),
            mode='w')

    # create environment/versions.tf
    write_file(
        filepath=f'{BASE_DIR}provision/environment/versions.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'versions.tf.j2',
            generated_license=GENERATED_LICENSE,
            storage_bucket_name=config.storage_bucket_name
        ),
        mode='w')

    # create provision_resources.sh
    write_and_chmod(
        filepath=GENERATED_RESOURCES_SH_FILE,
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH) / 'provision_resources.sh.j2',
            base_dir=BASE_DIR,
            generated_license=GENERATED_LICENSE
        ))

    # create state_bucket/main.tf
    write_file(
        filepath=f'{BASE_DIR}provision/state_bucket/main.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'main.tf.j2',
            generated_license=GENERATED_LICENSE
        ),
        mode='w')

    # create state_bucket/variables.tf
    write_file(
        filepath=f'{BASE_DIR}provision/state_bucket/variables.tf',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'variables.tf.j2',
            generated_license=GENERATED_LICENSE
        ),
        mode='w')

    # create state_bucket/variables.auto.tfvars
    write_file(
        filepath=f'{BASE_DIR}provision/state_bucket/variables.auto.tfvars',
        text=render_jinja(
            template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'variables.auto.tfvars.j2',
            project_id=project_id,
            storage_bucket_location=config.storage_bucket_location,
            storage_bucket_name=config.storage_bucket_name
        ),
        mode='w')
