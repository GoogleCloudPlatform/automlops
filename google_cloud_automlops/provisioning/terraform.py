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

"""Creates Terraform infrastructure object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.provisioning.base import Infrastructure

from google_cloud_automlops.utils.utils import (
    render_jinja,
    write_and_chmod,
    write_file
)

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_RESOURCES_SH_FILE,
    IAM_ROLES_RUNNER_SA,
    TERRAFORM_TEMPLATES_PATH
)

from google_cloud_automlops.utils.enums import (
    Deployer
)


class Terraform(Infrastructure):
    """Creates a Terraform specific Infrastructure object.

    Args:
        Infrastructure (object): Generic Infrastructure object.
    """
    def __init__(self, provision_credentials_key):
        """Initializes Terraform infrastructure object.

        Args:
            provision_credentials_key (str): Either a path to or the contents of a service account
                key file in JSON format.
        """
        super().__init__(provision_credentials_key)

    def build(self):
        """Creates all files needed to provision system infrastructure in terraform.
        
            Files created under AutoMLOps/
                provision/
                    environment/
                        data.tf
                        iam.tf
                        main.tf
                        outputs.tf
                        provider.tf
                        variables.tf
                        variables.auto.tfvars
                        versions.tf
                    state_bucket/
                        main.tf
                        variables.tf
                        variables.auto.tfvars
                scripts/
                    provision_resources.sh
        """

        # create environment/data.tf
        write_file(
            filepath=f'{BASE_DIR}provision/environment/data.tf',
            text=render_jinja(
                template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'data.tf.j2',
                generated_license=GENERATED_LICENSE,
                required_apis=self.required_apis,
                required_iam_roles=IAM_ROLES_RUNNER_SA,
                use_ci=self.use_ci
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
                artifact_repo_type=self.artifact_repo_type,
                base_dir=BASE_DIR,
                deployment_framework=self.deployment_framework,
                generated_license=GENERATED_LICENSE,
                generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
                naming_prefix=self.naming_prefix,
                pipeline_job_submission_service_type=self.pipeline_job_submission_service_type,
                schedule_pattern=self.schedule_pattern,
                source_repo_type=self.source_repo_type,
                use_ci=self.use_ci,
                vpc_connector=self.vpc_connector
            ),
            mode='w')

        # create environment/outputs.tf
        write_file(
            filepath=f'{BASE_DIR}provision/environment/outputs.tf',
            text=render_jinja(
                template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'outputs.tf.j2',
                artifact_repo_type=self.artifact_repo_type,
                deployment_framework=self.deployment_framework,
                generated_license=GENERATED_LICENSE,
                pipeline_job_submission_service_type=self.pipeline_job_submission_service_type,
                schedule_pattern=self.schedule_pattern,
                source_repo_type=self.source_repo_type,
                use_ci=self.use_ci
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
        if self.deployment_framework == Deployer.CLOUDBUILD.value:
            write_file(
                filepath=f'{BASE_DIR}provision/environment/variables.auto.tfvars',
                text=render_jinja(
                    template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.auto.tfvars.j2',
                    artifact_repo_location=self.artifact_repo_location,
                    artifact_repo_name=self.artifact_repo_name,
                    build_trigger_location=self.build_trigger_location,
                    build_trigger_name=self.build_trigger_name,
                    generated_license=GENERATED_LICENSE,
                    pipeline_job_runner_service_account=self.pipeline_job_runner_service_account,
                    pipeline_job_submission_service_location=self.pipeline_job_submission_service_location,
                    pipeline_job_submission_service_name=self.pipeline_job_submission_service_name,
                    project_id=self.project_id,
                    provision_credentials_key=self.provision_credentials_key,
                    pubsub_topic_name=self.pubsub_topic_name,
                    schedule_location=self.schedule_location,
                    schedule_name=self.schedule_name,
                    schedule_pattern=self.schedule_pattern,
                    source_repo_branch=self.source_repo_branch,
                    source_repo_name=self.source_repo_name,
                    storage_bucket_location=self.storage_bucket_location,
                    storage_bucket_name=self.storage_bucket_name,
                    vpc_connector=self.vpc_connector
                ),
                mode='w')

        #TODO: implement workload identity as optional
        if self.deployment_framework == Deployer.GITHUB_ACTIONS.value:
            write_file(
                filepath=f'{BASE_DIR}provision/environment/variables.auto.tfvars',
                text=render_jinja(
                    template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'variables.auto.tfvars.j2',
                    artifact_repo_location=self.artifact_repo_location,
                    artifact_repo_name=self.artifact_repo_name,
                    build_trigger_location=self.build_trigger_location,
                    build_trigger_name=self.build_trigger_name,
                    generated_license=GENERATED_LICENSE,
                    pipeline_job_runner_service_account=self.pipeline_job_runner_service_account,
                    pipeline_job_submission_service_location=self.pipeline_job_submission_service_location,
                    pipeline_job_submission_service_name=self.pipeline_job_submission_service_name,
                    project_id=self.project_id,
                    provision_credentials_key=self.provision_credentials_key,
                    pubsub_topic_name=self.pubsub_topic_name,
                    schedule_location=self.schedule_location,
                    schedule_name=self.schedule_name,
                    schedule_pattern=self.schedule_pattern,
                    source_repo_branch=self.source_repo_branch,
                    source_repo_name=self.source_repo_name,
                    storage_bucket_location=self.storage_bucket_location,
                    storage_bucket_name=self.storage_bucket_name,
                    vpc_connector=self.vpc_connector
                ),
                mode='w')

        # create environment/versions.tf
        write_file(
            filepath=f'{BASE_DIR}provision/environment/versions.tf',
            text=render_jinja(
                template_path=import_files(TERRAFORM_TEMPLATES_PATH + '.environment') / 'versions.tf.j2',
                generated_license=GENERATED_LICENSE,
                storage_bucket_name=self.storage_bucket_name
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
                project_id=self.project_id,
                storage_bucket_location=self.storage_bucket_location,
                storage_bucket_name=self.storage_bucket_name
            ),
            mode='w')
