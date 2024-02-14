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

"""Creates a generic services object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from abc import ABC, abstractmethod

from google_cloud_automlops.utils.utils import read_yaml_file
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_DEFAULTS_FILE
)


class Services(ABC):
    """The Services object will contain TODO: fill out what this does

    Args:
        ABC: Abstract class
    """

    def __init__(self) -> None:
        """Instantiates a generic Services object.
        """

    def build(self):
        """Constructs and writes a Dockerfile, requirements.txt, and
        main.py to the services/submission_service directory. 
        """

        # Read in defaults params
        defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
        self.pipeline_storage_path = defaults['pipelines']['pipeline_storage_path']
        self.pipeline_job_runner_service_account = defaults['gcp']['pipeline_job_runner_service_account']
        self.pipeline_job_submission_service_type = defaults['gcp']['pipeline_job_submission_service_type']
        self.project_id = defaults['gcp']['project_id']
        self.pipeline_job_submission_service_type = defaults['gcp']['pipeline_job_submission_service_type']

        # Set directory for files to be written to
        self.submission_service_base_dir = BASE_DIR + 'services/submission_service'

        self._build_main()
        self._build_dockerfile()
        self._build_requirements()

    @abstractmethod
    def _build_dockerfile(self):
        """Abstract method to create the Dockerfile file of the services/submission_service directory.
        """

    @abstractmethod
    def _build_requirements(self):
        """Abstract method to create the requirements.txt file of the services/submission_service directory.
        """

    @abstractmethod
    def _build_main(self):
        """Abstract method to create the main.py file of the services/submission_service directory.
        """
