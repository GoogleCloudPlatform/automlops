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

"""Creates Pulumi infrastructure object."""

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
    make_dirs,
    render_jinja,
    write_file,
)

from google_cloud_automlops.utils.enums import PulumiRuntime

from google_cloud_automlops.utils.constants import (
    GENERATED_LICENSE,
    PULUMI_TEMPLATES_PATH
)


class Pulumi(Infrastructure):
    """Creates a Pulumi specific Infrastructure object.

    Args:
        Infrastructure (object): Generic Infrastructure object.
    """
    def __init__(self,
                 provision_credentials_key: str):
        """Initializes Pulumi infrastructure object.

        Args:
            provision_credentials_key (str): Either a path to or the contents of a service account
                key file in JSON format.
        """
        super().__init__(provision_credentials_key)
        self.pipeline_model_name = self.naming_prefix
        self.region = self.storage_bucket_location
        self.cloudtasks_queue_name = self.naming_prefix
        self.pulumi_runtime = PulumiRuntime.PYTHON

        # Define the model name for the IaC configurations
        # remove special characters and spaces
        self.pipeline_model_name = ''.join(
            ['_' if c in ['.', '-', '/', ' '] else c for c in self.pipeline_model_name]).lower()

        self.storage_bucket_name = ''.join(
            ['_' if c in ['.', '/', ' '] else c for c in self.storage_bucket_name]).lower()

        self.artifact_repo_name = ''.join(
            ['-' if c in ['.', '_', '/', ' '] else c for c in self.artifact_repo_name]).lower()

        self.source_repo_name = ''.join(
            ['-' if c in ['.', '_', '/', ' '] else c for c in self.source_repo_name]).lower()

        self.cloudtasks_queue_name = ''.join(
            ['-' if c in ['.', '_', '/', ' '] else c for c in self.cloudtasks_queue_name]).lower()

        self.build_trigger_name = ''.join(
            ['-' if c in ['.', '_', '/', ' '] else c for c in self.build_trigger_name]).lower()

    def build(self):

        # create pulumi folder
        make_dirs([self.pipeline_model_name + '/'])
        pulumi_folder = self.pipeline_model_name + '/'

        # create Pulumi.yaml
        write_file(
            pulumi_folder + 'Pulumi.yaml',
            render_jinja(
                template_path=PULUMI_TEMPLATES_PATH / 'Pulumi.yaml.jinja',
                generated_license=GENERATED_LICENSE,
                pipeline_model_name=self.pipeline_model_name,
                pulumi_runtime=self.pulumi_runtime.value),
            'w'
        )

        # create Pulumi.dev.yaml
        write_file(
            pulumi_folder + 'Pulumi.dev.yaml',
            render_jinja(
                template_path=PULUMI_TEMPLATES_PATH / 'Pulumi.dev.yaml.jinja',
                generated_license=GENERATED_LICENSE,
                project_id=self.project_id,
                pipeline_model_name=self.pipeline_model_name,
                region=self.region,
                storage_bucket_name=self.storage_bucket_name),
            'w'
        )

        # create python __main__.py
        if self.pulumi_runtime == PulumiRuntime.PYTHON:
            write_file(
                pulumi_folder + '__main__.py',
                render_jinja(
                    template_path=PULUMI_TEMPLATES_PATH / 'python/__main__.py.jinja',
                    generated_license=GENERATED_LICENSE,
                    artifact_repo_name=self.artifact_repo_name,
                    source_repo_name=self.source_repo_name,
                    cloudtasks_queue_name=self.cloudtasks_queue_name,
                    build_trigger_name=self.build_trigger_name),
                'w'
            )
