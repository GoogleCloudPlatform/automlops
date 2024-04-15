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

"""Creates GitHub Actions Deployment object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.utils.utils import (
    render_jinja,
    write_file
)

from google_cloud_automlops.utils.constants import (
    GENERATED_GITHUB_ACTIONS_FILE,
    COMPONENT_BASE_RELATIVE_PATH,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GITHUB_ACTIONS_TEMPLATES_PATH
)

from google_cloud_automlops.deployments.base import Deployment


class GitHubActions(Deployment):
    """The Deployment object represents all information and functions to create an AutoMLOps
    system's deployment.
    """
    def __init__(self,
                 project_number: str,
                 workload_identity_pool: str,
                 workload_identity_provider: str,
                 workload_identity_service_account: str):
        """Initializes a GitHub Actions object by reading in default attributes.

        Args:
            project_number (str): The project number.
            workload_identity_pool (str): Pool for workload identity federation.
            workload_identity_provider (str): Provider for workload identity federation.
            workload_identity_service_account (str): Service account for workload identity federation (specify the full string).
        """
        super().__init__()
        self.project_number = project_number
        self.workload_identity_pool = workload_identity_pool
        self.workload_identity_provider = workload_identity_provider
        self.workload_identity_service_account = workload_identity_service_account

    def build(self):
        """Constructs Github actions yaml at AutoMLOps/.github/workflows/github_actions.yaml.
        """
        # Write github actions config
        write_file(
            filepath=GENERATED_GITHUB_ACTIONS_FILE,
            text=render_jinja(
                template_path=import_files(GITHUB_ACTIONS_TEMPLATES_PATH) / 'github_actions.yaml.j2',
                artifact_repo_location=self.artifact_repo_location,
                artifact_repo_name=self.artifact_repo_name,
                component_base_relative_path=COMPONENT_BASE_RELATIVE_PATH,
                generated_license=GENERATED_LICENSE,
                generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
                naming_prefix=self.naming_prefix,
                project_id=self.project_id,
                project_number=self.project_number,
                pubsub_topic_name=self.pubsub_topic_name,
                source_repo_branch=self.source_repo_branch,
                use_ci=self.use_ci,
                workload_identity_pool=self.workload_identity_pool,
                workload_identity_provider=self.workload_identity_provider,
                workload_identity_service_account=self.workload_identity_service_account
            ),
            mode='w')
