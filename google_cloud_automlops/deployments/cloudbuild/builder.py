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

from google_cloud_automlops.utils.utils import (
    render_jinja,
    write_file
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    CLOUDBUILD_TEMPLATES_PATH,
    GENERATED_CLOUDBUILD_FILE,
    COMPONENT_BASE_RELATIVE_PATH,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH
)

from google_cloud_automlops.deployments.configs import CloudBuildConfig

def build(config: CloudBuildConfig):
    """Constructs scripts for resource deployment and running Kubeflow pipelines.

    Args:
        config.artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        config.artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        config.naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        config.project_id: The project ID.        
        config.pubsub_topic_name: The name of the pubsub topic to publish to.
        config.use_ci: Flag that determines whether to use Cloud CI/CD.
    """
    # Write cloud build config
    component_base_relative_path = COMPONENT_BASE_RELATIVE_PATH if config.use_ci else f'{BASE_DIR}{COMPONENT_BASE_RELATIVE_PATH}'
    write_file(
        filepath=GENERATED_CLOUDBUILD_FILE, 
        text=render_jinja(
            template_path=import_files(CLOUDBUILD_TEMPLATES_PATH) / 'cloudbuild.yaml.j2',
            artifact_repo_location=config.artifact_repo_location,
            artifact_repo_name=config.artifact_repo_name,
            component_base_relative_path=component_base_relative_path,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            naming_prefix=config.naming_prefix,
            project_id=config.project_id,
            pubsub_topic_name=config.pubsub_topic_name,
            use_ci=config.use_ci),
        mode='w')
