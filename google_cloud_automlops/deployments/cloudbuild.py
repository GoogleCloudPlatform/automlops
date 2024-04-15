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

"""Creates CloudBuild deployment object."""

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
    BASE_DIR,
    CLOUDBUILD_TEMPLATES_PATH,
    GENERATED_CLOUDBUILD_FILE,
    COMPONENT_BASE_RELATIVE_PATH,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH
)

from google_cloud_automlops.deployments.base import Deployment


class CloudBuild(Deployment):
    """The Deployment object represents all information and functions to create an AutoMLOps
    system's deployment.
    """
    def __init__(self):
        """Initializes a GitHub Actions object by reading in default attributes.
        """
        super().__init__()

    def build(self):
        """Constructs CloudBuild yaml at AutoMLOps/cloudbuild.yaml.
        """
        # Write cloud build config
        component_base_relative_path = COMPONENT_BASE_RELATIVE_PATH if self.use_ci else f'{BASE_DIR}{COMPONENT_BASE_RELATIVE_PATH}'
        write_file(
            filepath=GENERATED_CLOUDBUILD_FILE,
            text=render_jinja(
                template_path=import_files(CLOUDBUILD_TEMPLATES_PATH) / 'cloudbuild.yaml.j2',
                artifact_repo_location=self.artifact_repo_location,
                artifact_repo_name=self.artifact_repo_name,
                component_base_relative_path=component_base_relative_path,
                generated_license=GENERATED_LICENSE,
                generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
                naming_prefix=self.naming_prefix,
                project_id=self.project_id,
                pubsub_topic_name=self.pubsub_topic_name,
                use_ci=self.use_ci),
            mode='w')
