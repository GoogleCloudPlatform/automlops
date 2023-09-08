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

"""Builds Pulumi Files"""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import

from jinja2 import Template

from google_cloud_automlops.utils.utils import (
    write_file,
    make_dirs,
)

from google_cloud_automlops.utils.constants import (
    GENERATED_LICENSE,
    PULUMI_TEMPLATES_PATH
)

from google_cloud_automlops.provisioning.enums import PulumiRuntime
from google_cloud_automlops.provisioning.configs import PulumiConfig


def build(
    project_id: str,
    config: PulumiConfig,
):
    """Constructs and writes pulumi scripts: Generates infrastructure using pulumi resource management style.

    Args:
        project_id: The project ID.
        config.pipeline_model_name: Name of the model being deployed.
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.
        config.artifact_repo_name: name of the artifact registry for the model infrastructure.
        config.source_repo_name: source repository used as part of the the model infra.
        config.cloudtasks_queue_name: name of the task queue used for model scheduling.
        config.cloud_build_trigger_name: name of the cloud build trigger for the model infra.
        config.pulumi_runtime: The pulumi runtime option (default: PulumiRuntime.PYTHON).
    """

    # Define the model name for the IaC configurations
    # remove special characters and spaces
    pipeline_model_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.pipeline_model_name]).lower()

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

    # create pulumi folder
    make_dirs([pipeline_model_name + '/'])
    pulumi_folder = pipeline_model_name + '/'

    # create Pulumi.yaml
    write_file(pulumi_folder + 'Pulumi.yaml', _create_pulumi_yaml_jinja(
        pipeline_model_name=pipeline_model_name,
        pulumi_runtime=config.pulumi_runtime), 'w'
    )

    # create Pulumi.dev.yaml
    write_file(pulumi_folder + 'Pulumi.dev.yaml', _create_pulumi_dev_yaml_jinja(
        project_id=project_id,
        pipeline_model_name=pipeline_model_name,
        region=config.region,
        gcs_bucket_name=gcs_bucket_name), 'w'
    )

    # create python __main__.py
    if config.pulumi_runtime == PulumiRuntime.PYTHON:
        write_file(pulumi_folder + '__main__.py', _create_main_python_jinja(
            artifact_repo_name=artifact_repo_name,
            source_repo_name=source_repo_name,
            cloudtasks_queue_name=cloudtasks_queue_name,
            cloud_build_trigger_name=cloud_build_trigger_name), 'w'
        )


def _create_pulumi_yaml_jinja(
    pipeline_model_name: str,
    pulumi_runtime: str,
) -> str:
    """Generates code for Pulumi.yaml, the pulumi script that contains details to deploy project's GCP environment.

    Args:
        config.pipeline_model_name: Name of the model being deployed.
        config.pulumi_runtime: The pulumi runtime option (default: PulumiRuntime.PYTHON).

    Returns:
        str: Pulumi.yaml config script.
    """

    with open(PULUMI_TEMPLATES_PATH / 'Pulumi.yaml.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            pipeline_model_name=pipeline_model_name,
            pulumi_runtime=pulumi_runtime.value,
        )


def _create_pulumi_dev_yaml_jinja(
        project_id: str,
        pipeline_model_name: str,
        region: str,
        gcs_bucket_name: str,
) -> str:
    """Generates code for Pulumi.dev.yaml, the pulumi script that contains details to deploy dev environment config.

    Args:
        project_id: The project ID.
        config.pipeline_model_name: Name of the model being deployed.
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.

    Returns:
        str: Pulumi.dev.yaml config script.
    """

    with open(PULUMI_TEMPLATES_PATH / 'Pulumi.dev.yaml.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            project_id=project_id,
            pipeline_model_name=pipeline_model_name,
            region=region,
            gcs_bucket_name=gcs_bucket_name,
        )


def _create_main_python_jinja(
    artifact_repo_name,
    source_repo_name,
    cloudtasks_queue_name,
    cloud_build_trigger_name,
) -> str:
    """Generates code for __main__.py, the pulumi script that creates the primary resources.

    Args:
        artifact_repo_name: name of the artifact registry for the model infrastructure.
        source_repo_name: source repository used as part of the the model infra.
        cloudtasks_queue_name: name of the task queue used for model scheduling.
        cloud_build_trigger_name: name of the cloud build trigger for the model infra.

    Returns:
        str: Main pulumi script.
    """

    with open(PULUMI_TEMPLATES_PATH / 'python/__main__.py.jinja', 'r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            artifact_repo_name=artifact_repo_name,
            source_repo_name=source_repo_name,
            cloudtasks_queue_name=cloudtasks_queue_name,
            cloud_build_trigger_name=cloud_build_trigger_name,
        )
