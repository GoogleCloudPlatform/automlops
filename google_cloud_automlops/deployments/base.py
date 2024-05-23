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

"""Creates generic deployment object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from google_cloud_automlops.utils.constants import GENERATED_DEFAULTS_FILE

from google_cloud_automlops.utils.utils import read_yaml_file


class Deployment():
    """The Deployment object represents all information and functions to create an AutoMLOps
    system's deployment.
    """
    def __init__(self):
        """Initializes a generic Deployment object by reading in default attributes.
        """
        defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
        self.use_ci = defaults['tooling']['use_ci']
        self.artifact_repo_location = defaults['gcp']['artifact_repo_location']
        self.artifact_repo_name = defaults['gcp']['artifact_repo_name']
        self.deployment_framework = defaults['tooling']['deployment_framework']
        self.naming_prefix = defaults['gcp']['naming_prefix']
        self.project_id = defaults['gcp']['project_id']
        self.pubsub_topic_name = defaults['gcp']['pubsub_topic_name'] if self.use_ci else None
        self.source_repo_branch = defaults['gcp']['source_repository_branch'] if self.use_ci else None
        self.source_repo_type = defaults['gcp']['source_repository_type'] if self.use_ci else None

    def build(self):
        """Abstract method to create all files related to CI/CD deployments.

        Raises:
            NotImplementedError: The subclass has not defined the `build` method.
        """
        raise NotImplementedError('Subclass needs to define this.')
