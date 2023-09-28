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

"""Builds KFP components and pipeline."""

# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from jinja2 import Template

from google_cloud_automlops.utils.utils import write_file
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    DEFAULT_SOURCE_REPO_BRANCH,
    GITHUB_ACTIONS_TEMPLATES_PATH,
    GENERATED_GITHUB_ACTIONS_FILE,
    GENERATED_COMPONENT_BASE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH
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
        config.use_ci: Flag that determines whether to use Cloud CI/CD.
    """
    # Write github actions config
    write_file(GENERATED_GITHUB_ACTIONS_FILE, create_github_actions_jinja(
        config.artifact_repo_location,
        config.artifact_repo_name,
        config.naming_prefix,
        config.project_id,
        config.project_number,
        config.pubsub_topic_name,
        config.use_ci,
        config.workload_identity_pool,
        config.workload_identity_provider,
        config.workload_identity_service_account), 'w')

def create_github_actions_jinja(
        artifact_repo_location: str,
        artifact_repo_name: str,
        naming_prefix: str,
        project_id: str,
        project_number: str, 
        pubsub_topic_name: str,
        use_ci: bool,
        workload_identity_pool: str,
        workload_identity_provider: str,
        workload_identity_service_account: str) -> str:
    """Generates content for the github_actions.yaml, to be written to the .github directory.
        This file contains the ci/cd manifest for AutoMLOps.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        project_id: The project ID.        
        pubsub_topic_name: The name of the pubsub topic to publish to.
        use_ci: Flag that determines whether to use Cloud CI/CD.

    Returns:
        str: Contents of github_actions.yaml.
    """
    template_file = import_files(GITHUB_ACTIONS_TEMPLATES_PATH) / 'github_actions.yaml.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            artifact_repo_location=artifact_repo_location,
            artifact_repo_name=artifact_repo_name,
            base_dir=BASE_DIR,
            generated_component_base=GENERATED_COMPONENT_BASE,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            naming_prefix=naming_prefix,
            project_id=project_id,
            project_number=project_number,
            pubsub_topic_name=pubsub_topic_name,
            source_repo_branch=DEFAULT_SOURCE_REPO_BRANCH,
            use_ci=use_ci,
            workload_identity_pool=workload_identity_pool,
            workload_identity_provider=workload_identity_provider,
            workload_identity_service_account=workload_identity_service_account)
