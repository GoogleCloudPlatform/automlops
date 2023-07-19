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
# pylint: disable=unused-import

from jinja2 import Template

from AutoMLOps.utils.utils import (
    write_file,
    make_dirs,
)

from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    TERRAFORM_TEMPLATE_PATH
)

from AutoMLOps.iac.configs import TerraformConfig


def builder(
    project_id: str,
    config: TerraformConfig,
):
    """Constructs and writes terraform scripts: Generates infrastructure using terraform hcl resource management style.

    Args:
        project_id: The project ID.
        provider: The provider option (default: Provider.TERRAFORM).
        config.pipeline_model_name: Name of the model being deployed.
        config.creds_tf_var_name: Name of tf variable with project access credentials json key
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure
        config.artifact_repo_name: name of the artifact registry for the model infrastructure
        config.source_repo_name: source repository used as part of the the model infra
        config.cloudtasks_queue_name: name of the task queue used for model scheduling
        config.cloud_build_trigger_name: name of the cloud build trigger for the model infra
        config.workspace_name: Name of the terraform cloud workspace.
    """

    # Define the model name for the IaC configurations
    # remove special characters and spaces
    pipeline_model_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.pipeline_model_name]).lower()

    creds_tf_var_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.creds_tf_var_name]).upper()

    workspace_name = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in config.workspace_name]).lower()

    project_id = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in project_id]).lower()

    gcs_bucket_name = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in config.gcs_bucket_name]).lower()

    artifact_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.artifact_repo_name]).lower()

    source_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.source_repo_name]).lower()

    cloudtasks_queue_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloudtasks_queue_name]).lower()

    cloud_build_trigger_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloud_build_trigger_name]).lower()

    # create terraform folder
    make_dirs([pipeline_model_name + '/'])
    terraform_folder = pipeline_model_name + '/'

    # create variables.tf
    write_file(terraform_folder + 'variables.tf', _create_variables_tf_jinja(
        creds_tf_var_name=creds_tf_var_name,), 'w+'
    )

    # create terraform.tfvars
    write_file(terraform_folder + 'terraform.tfvars', _create_terraform_tfvars_jinja(
        creds_tf_var_name=creds_tf_var_name,), 'w+'
    )

    # create provider.tf
    write_file(terraform_folder + 'provider.tf', _create_provider_tf_jinja(
        creds_tf_var_name=creds_tf_var_name,), 'w+'
    )

    # create outputs.tf
    write_file(
        terraform_folder + 'outputs.tf',
        _create_outputs_tf_jinja(), 'w+'
    )

    # create data.tf
    write_file(terraform_folder + 'data.tf', _create_data_tf_jinja(
        workspace_name=workspace_name,
        project_id=project_id,
        pipeline_model_name=pipeline_model_name,
        region=config.region), 'w+'
    )

    # create main.tf
    write_file(terraform_folder + 'main.tf', _create_main_tf_jinja(
        pipeline_model_name=pipeline_model_name,
        region=config.region,
        gcs_bucket_name=gcs_bucket_name,
        artifact_repo_name=artifact_repo_name,
        source_repo_name=source_repo_name,
        cloudtasks_queue_name=cloudtasks_queue_name,
        cloud_build_trigger_name=cloud_build_trigger_name,), 'w+'
    )

    # create iam.tf
    write_file(terraform_folder + 'iam.tf', _create_iam_tf_jinja(), 'w+')


def _create_variables_tf_jinja(
        creds_tf_var_name: str,
) -> str:
    """Generates code for variables.tf, the terraform hcl script that contains variables used to deploy project's environment.

    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: variables.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'variables.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            creds_tf_var_name=creds_tf_var_name,
        )


def _create_terraform_tfvars_jinja(
        creds_tf_var_name: str,
) -> str:
    """Generates code for terraform.tfvars, the terraform hcl script that contains teraform variables used to deploy project's environment.

    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: terraform.tfvars config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'terraform.tfvars.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            creds_tf_var_name=creds_tf_var_name,
        )


def _create_provider_tf_jinja(
        creds_tf_var_name: str,
) -> str:
    """Generates code for provider.tf, the terraform hcl script that contains teraform providers used to deploy project's environment.

    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: provider.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'provider.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            creds_tf_var_name=creds_tf_var_name,
        )


def _create_outputs_tf_jinja() -> str:
    """Generates code for outputs.tf, the terraform hcl script that contains outputs from project's environment.
    Args:
        takes no arguments.

    Returns:
        str: outputs.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'outputs.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
        )


def _create_data_tf_jinja(
    workspace_name: str,
    project_id: str,
    region: str,
    pipeline_model_name: str,
) -> str:
    """Generates code for data.tf, the terraform hcl script that contains terraform remote backend and org project details.

    Args:
        workspace_name: Name of the terraform cloud workspace.
        project_id: The project ID.
        region: region used in gcs infrastructure config.
        pipeline_model_name: Name of the model being deployed.

    Returns:
        str: data.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'data.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            workspace_name=workspace_name,
            project_id=project_id,
            region=region,
            pipeline_model_name=pipeline_model_name,
        )


def _create_main_tf_jinja(
    pipeline_model_name: str,
    region: str,
    gcs_bucket_name: str,
    artifact_repo_name: str,
    source_repo_name: str,
    cloudtasks_queue_name,
    cloud_build_trigger_name,
) -> str:
    """Generates code for main.tf, the terraform hcl script that contains terraform resources configs to deploy resources in the gcs project.

    Args:
        pipeline_model_name: Name of the model being deployed.
        region: region used in gcs infrastructure config.
        gcs_bucket_name: gcs bucket name to use as part of the model infrastructure
        artifact_repo_name: name of the artifact registry for the model infrastructure
        source_repo_name: source repository used as part of the the model infra
        cloudtasks_queue_name: name of the task queue used for model scheduling
        cloud_build_trigger_name: name of the cloud build trigger for the model infra

    Returns:
        str: main.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'main.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            pipeline_model_name=pipeline_model_name,
            region=region,
            gcs_bucket_name=gcs_bucket_name,
            artifact_repo_name=artifact_repo_name,
            source_repo_name=source_repo_name,
            cloudtasks_queue_name=cloudtasks_queue_name,
            cloud_build_trigger_name=cloud_build_trigger_name,
        )


def _create_iam_tf_jinja() -> str:
    """Generates code for iam.tf, the terraform hcl script that contains service accounts iam bindings for project's environment.

    Args:
        takes no arguments.

    Returns:
        str: iam.tf config script.
    """

    with open(TERRAFORM_TEMPLATE_PATH / 'iam.tf.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
        )
