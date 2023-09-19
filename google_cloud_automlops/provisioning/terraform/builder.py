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

from jinja2 import Template

from google_cloud_automlops.utils.utils import (
    get_required_apis,
    read_yaml_file,
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

from google_cloud_automlops.provisioning.configs import TerraformConfig

def build(
    project_id: str,
    config: TerraformConfig,
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
    required_apis = list(get_required_apis(defaults))
    # create environment/data.tf
    write_file(f'{BASE_DIR}provision/environment/data.tf', create_environment_data_tf_jinja(
        required_apis=required_apis), 'w')
    # create environment/iam.tf
    write_file(f'{BASE_DIR}provision/environment/iam.tf', create_environment_iam_tf_jinja(), 'w')
    # create environment/main.tf
    write_file(f'{BASE_DIR}provision/environment/main.tf', create_environment_main_tf_jinja(
        artifact_repo_type=config.artifact_repo_type,
        deployment_framework=config.deployment_framework,
        naming_prefix=config.naming_prefix,
        pipeline_job_submission_service_type=config.pipeline_job_submission_service_type,
        schedule_pattern=config.schedule_pattern,
        source_repo_type=config.source_repo_type,
        use_ci=config.use_ci,
        vpc_connector=config.vpc_connector), 'w')
    # create environment/outputs.tf
    write_file(f'{BASE_DIR}provision/environment/outputs.tf', create_environment_outputs_tf_jinja(
        artifact_repo_type=config.artifact_repo_type,
        deployment_framework=config.deployment_framework,
        pipeline_job_submission_service_type=config.pipeline_job_submission_service_type,
        schedule_pattern=config.schedule_pattern,
        source_repo_type=config.source_repo_type,
        use_ci=config.use_ci), 'w')
    # create environment/provider.tf
    write_file(f'{BASE_DIR}provision/environment/provider.tf', create_environment_provider_tf_jinja(), 'w')
    # create environment/variables.tf
    write_file(f'{BASE_DIR}provision/environment/variables.tf', create_environment_variables_tf_jinja(), 'w')
    # create environment/variables.auto.tfvars
    write_file(f'{BASE_DIR}provision/environment/variables.auto.tfvars', create_environment_variables_auto_tfvars_jinja(
        artifact_repo_location=config.artifact_repo_location,
        artifact_repo_name=config.artifact_repo_name,
        build_trigger_location=config.build_trigger_location,
        build_trigger_name=config.build_trigger_name,
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
        vpc_connector=config.vpc_connector), 'w')
    # create environment/versions.tf
    write_file(f'{BASE_DIR}provision/environment/versions.tf', create_environment_versions_tf_jinja(storage_bucket_name=config.storage_bucket_name), 'w')
    # create provision_resources.sh
    write_and_chmod(GENERATED_RESOURCES_SH_FILE, create_provision_resources_script_jinja())
    # create state_bucket/main.tf
    write_file(f'{BASE_DIR}provision/state_bucket/main.tf', create_state_bucket_main_tf_jinja(), 'w')
    # create state_bucket/variables.tf
    write_file(f'{BASE_DIR}provision/state_bucket/variables.tf', create_state_bucket_variables_tf_jinja(), 'w')
    # create state_bucket/variables.auto.tfvars
    write_file(f'{BASE_DIR}provision/state_bucket/variables.auto.tfvars', create_state_bucket_variables_auto_tfvars_jinja(
        project_id=project_id,
        storage_bucket_location=config.storage_bucket_location,
        storage_bucket_name=config.storage_bucket_name), 'w')


def create_environment_data_tf_jinja(required_apis: list) -> str:
    """Generates code for environment/data.tf, the terraform hcl script that contains terraform remote backend and org project details.

    Args:
        required_apis: List of APIs that are required to run the service.

    Returns:
        str: environment/data.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'data.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            required_apis=required_apis)


def create_environment_iam_tf_jinja() -> str:
    """Generates code for environment/iam.tf, the terraform hcl script that contains service accounts iam bindings for project's environment.

    Returns:
        str: environment/iam.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'iam.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            required_iam_roles=IAM_ROLES_RUNNER_SA)


def create_environment_main_tf_jinja(
    artifact_repo_type: str,
    deployment_framework: str,
    naming_prefix: str,
    pipeline_job_submission_service_type: str,
    schedule_pattern: str,
    source_repo_type: str,
    use_ci: bool,
    vpc_connector: str) -> str:
    """Generates code for environment/main.tf, the terraform hcl script that contains terraform resources configs to deploy resources in the project.

    Args:
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.

    Returns:
        str: environment/main.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'main.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            artifact_repo_type=artifact_repo_type,
            base_dir=BASE_DIR,
            deployment_framework=deployment_framework,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            naming_prefix=naming_prefix,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type,
            schedule_pattern=schedule_pattern,
            source_repo_type=source_repo_type,
            use_ci=use_ci,
            vpc_connector=vpc_connector)


def create_environment_outputs_tf_jinja(
    artifact_repo_type: str,
    deployment_framework: str,
    pipeline_job_submission_service_type: str,
    schedule_pattern: str,
    source_repo_type: str,
    use_ci: bool) -> str:
    """Generates code for environment/outputs.tf, the terraform hcl script that contains outputs from project's environment.

    Args:
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        use_ci: Flag that determines whether to use Cloud CI/CD.

    Returns:
        str: environment/outputs.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'outputs.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            artifact_repo_type=artifact_repo_type,
            deployment_framework=deployment_framework,
            generated_license=GENERATED_LICENSE,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type,
            schedule_pattern=schedule_pattern,
            source_repo_type=source_repo_type,
            use_ci=use_ci)


def create_environment_provider_tf_jinja() -> str:
    """Generates code for environment/provider.tf, the terraform hcl script that contains teraform providers used to deploy project's environment.

    Returns:
        str: environment/provider.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'provider.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE)


def create_environment_variables_tf_jinja() -> str:
    """Generates code for environment/variables.tf, the terraform hcl script that contains variables used to deploy project's environment.

    Returns:
        str: environment/variables.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE)


def create_environment_variables_auto_tfvars_jinja(
    artifact_repo_location: str,
    artifact_repo_name: str,
    build_trigger_location: str,
    build_trigger_name: str,
    pipeline_job_runner_service_account: str,
    pipeline_job_submission_service_location: str,
    pipeline_job_submission_service_name: str,
    project_id: str,
    provision_credentials_key: str,
    pubsub_topic_name: str,
    schedule_location: str,
    schedule_name: str,
    schedule_pattern: str,
    source_repo_branch: str,
    source_repo_name: str,
    storage_bucket_location: str,
    storage_bucket_name: str,
    vpc_connector: str) -> str:
    """Generates code for environment/variables.auto.tfvars, the terraform hcl script that contains teraform arguments for variables used to deploy project's environment.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        build_trigger_location: The location of the build trigger (for cloud build).
        build_trigger_name: The name of the build trigger (for cloud build).
        pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        project_id: The project ID.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        vpc_connector: The name of the vpc connector to use.

    Returns:
        str: environment/variables.auto.tfvars file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.auto.tfvars.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            artifact_repo_location=artifact_repo_location,
            artifact_repo_name=artifact_repo_name,
            build_trigger_location=build_trigger_location,
            build_trigger_name=build_trigger_name,
            generated_license=GENERATED_LICENSE,
            pipeline_job_runner_service_account=pipeline_job_runner_service_account,
            pipeline_job_submission_service_location=pipeline_job_submission_service_location,
            pipeline_job_submission_service_name=pipeline_job_submission_service_name,
            project_id=project_id,
            provision_credentials_key=provision_credentials_key,
            pubsub_topic_name=pubsub_topic_name,
            schedule_location=schedule_location,
            schedule_name=schedule_name,
            schedule_pattern=schedule_pattern,
            source_repo_branch=source_repo_branch,
            source_repo_name=source_repo_name,
            storage_bucket_location=storage_bucket_location,
            storage_bucket_name=storage_bucket_name,
            vpc_connector=vpc_connector)


def create_environment_versions_tf_jinja(storage_bucket_name: str) -> str:
    """Generates code for environment/versions.tf, the terraform hcl script that contains teraform version information.
    Args:
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.

    Returns:
        str: environment/versions.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'versions.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            storage_bucket_name=storage_bucket_name)


def create_provision_resources_script_jinja() -> str:
    """Generates code for provision_resources.sh which sets up the project's environment using terraform.

    Returns:
        str: provision_resources.sh shell script.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH) / 'provision_resources.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            base_dir=BASE_DIR,
            generated_license=GENERATED_LICENSE)


def create_state_bucket_variables_tf_jinja() -> str:
    """Generates code for state_bucket/variables.tf, the terraform hcl script that contains variables used for the state_bucket.

    Returns:
        str: state_bucket/variables.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'variables.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE)


def create_state_bucket_variables_auto_tfvars_jinja(
    project_id: str,
    storage_bucket_location: str,
    storage_bucket_name: str) -> str:
    """Generates code for state_bucket/variables.auto.tfvars, the terraform hcl script that contains teraform arguments for variables used for the state_bucket.
       Uses the string f'{storage_bucket_name}-bucket-tfstate' for the name of the storage state bucket.

    Args:
        project_id: The project ID.
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.

    Returns:
        str: environment/variables.auto.tfvars file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'variables.auto.tfvars.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            project_id=project_id,
            storage_bucket_location=storage_bucket_location,
            storage_bucket_name=storage_bucket_name)


def create_state_bucket_main_tf_jinja() -> str:
    """Generates code for state_bucket/main.tf, the terraform hcl script that contains terraform resources configs to create the state_bucket.

    Returns:
        str: state_bucket/main.tf file.
    """
    template_file = import_files(TERRAFORM_TEMPLATES_PATH + '.state_bucket') / 'main.tf.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE)
