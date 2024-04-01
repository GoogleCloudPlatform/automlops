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

"""Builds KFP components and pipeline."""

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

from google_cloud_automlops.deployments.configs import GitHubActionsConfig

def build(config: GitHubActionsConfig):
    """Constructs scripts for resource deployment and running Kubeflow pipelines.

    Args:
        config.artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        config.artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        config.naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        config.project_id: The project ID.
        config.project_number: The project number.
        config.pubsub_topic_name: The name of the pubsub topic to publish to.
        config.source_repo_branch: The branch to use in the source repository.
        config.use_ci: Flag that determines whether to use Cloud CI/CD.
        config.workload_identity_pool: Pool for workload identity federation. 
        config.workload_identity_provider: Provider for workload identity federation.
        config.workload_identity_service_account: Service account for workload identity federation. 
    """
    # Write github actions config
    write_file(
        filepath=GENERATED_GITHUB_ACTIONS_FILE,
        text=render_jinja(
            template_path=import_files(GITHUB_ACTIONS_TEMPLATES_PATH) / 'github_actions.yaml.j2',
            artifact_repo_location=config.artifact_repo_location,
            artifact_repo_name=config.artifact_repo_name,
            component_base_relative_path=COMPONENT_BASE_RELATIVE_PATH,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            naming_prefix=config.naming_prefix,
            project_id=config.project_id,
            project_number=config.project_number,
            pubsub_topic_name=config.pubsub_topic_name,
            source_repo_branch=config.source_repo_branch,
            use_ci=config.use_ci,
            workload_identity_pool=config.workload_identity_pool,
            workload_identity_provider=config.workload_identity_provider,
            workload_identity_service_account=config.workload_identity_service_account
        ),
        mode='w')
