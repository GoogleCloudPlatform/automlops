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

"""Creates generic infrastructure object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from google_cloud_automlops.utils.constants import (
    DEFAULT_SCHEDULE_PATTERN,
    GENERATED_DEFAULTS_FILE
)

from google_cloud_automlops.utils.enums import (
    ArtifactRepository,
    Orchestrator,
    PipelineJobSubmitter
)

from google_cloud_automlops.utils.utils import (
    read_yaml_file
)


class Infrastructure():
    """The Infrastructure object represents all information and functions to create an AutoMLOps
    system's infrastructure.
    """
    def __init__(self, provision_credentials_key):
        """Initializes a generic Infrastructure object by reading in default attributes.

        Args:
            provision_credentials_key (str): Either a path to or the contents of a service account
                key file in JSON format.
        """
        defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
        self.use_ci = defaults['tooling']['use_ci']
        self.artifact_repo_location = defaults['gcp']['artifact_repo_location']
        self.artifact_repo_name = defaults['gcp']['artifact_repo_name']
        self.artifact_repo_type = defaults['gcp']['artifact_repo_type']
        self.build_trigger_location = defaults['gcp']['build_trigger_location'] if self.use_ci else None
        self.build_trigger_name = defaults['gcp']['build_trigger_name'] if self.use_ci else None
        self.deployment_framework = defaults['tooling']['deployment_framework']
        self.naming_prefix = defaults['gcp']['naming_prefix']
        self.orchestration_framework = defaults['tooling']['orchestration_framework']
        self.pipeline_job_runner_service_account = defaults['gcp']['pipeline_job_runner_service_account']
        self.pipeline_job_submission_service_location = defaults['gcp']['pipeline_job_submission_service_location'] if self.use_ci else None
        self.pipeline_job_submission_service_name = defaults['gcp']['pipeline_job_submission_service_name'] if self.use_ci else None
        self.pipeline_job_submission_service_type = defaults['gcp']['pipeline_job_submission_service_type'] if self.use_ci else None
        self.project_id = defaults['gcp']['project_id']
        self.provision_credentials_key = provision_credentials_key
        self.pubsub_topic_name = defaults['gcp']['pubsub_topic_name'] if self.use_ci else None
        self.schedule_location = defaults['gcp']['schedule_location'] if self.use_ci else None
        self.schedule_name = defaults['gcp']['schedule_name'] if self.use_ci else None
        self.schedule_pattern = defaults['gcp']['schedule_pattern'] if self.use_ci else None
        self.setup_model_monitoring = defaults['gcp']['setup_model_monitoring']
        self.source_repo_branch = defaults['gcp']['source_repository_branch'] if self.use_ci else None
        self.source_repo_name = defaults['gcp']['source_repository_name'] if self.use_ci else None
        self.source_repo_type = defaults['gcp']['source_repository_type'] if self.use_ci else None
        self.storage_bucket_location = defaults['gcp']['storage_bucket_location']
        self.storage_bucket_name = defaults['gcp']['storage_bucket_name']

        self.vpc_connector = defaults['gcp']['vpc_connector'] if self.use_ci else None

        self.required_apis = self._get_required_apis()

    def build(self):
        """Abstract method to create all files in the provision/ folder, and associated scripts.

        Raises:
            NotImplementedError: The subclass has not defined the `build` method.
        """
        raise NotImplementedError('Subclass needs to define this.')

    def _get_required_apis(self):
        """Returns the list of required APIs based on the user tooling selection determined during
        the generate() step.

        Returns:
            list: Required APIs.
        """
        required_apis = [
            'cloudbuild.googleapis.com',
            'cloudresourcemanager.googleapis.com',
            'compute.googleapis.com',
            'iamcredentials.googleapis.com',
            'iam.googleapis.com',
            'pubsub.googleapis.com',
            'storage.googleapis.com']
        if self.orchestration_framework == Orchestrator.KFP.value:
            required_apis.append('aiplatform.googleapis.com')
        if self.artifact_repo_type == ArtifactRepository.ARTIFACT_REGISTRY.value:
            required_apis.append('artifactregistry.googleapis.com')
        # if defaults['tooling']['deployment_framework'] == Deployer.CLOUDBUILD.value:
        #     required_apis.add('cloudbuild.googleapis.com')
        if self.use_ci:
            if self.schedule_pattern != DEFAULT_SCHEDULE_PATTERN:
                required_apis.append('cloudscheduler.googleapis.com')
            if self.pipeline_job_submission_service_type == PipelineJobSubmitter.CLOUD_RUN.value:
                required_apis.append('run.googleapis.com')
            if self.pipeline_job_submission_service_type == PipelineJobSubmitter.CLOUD_FUNCTIONS.value:
                required_apis.append('cloudfunctions.googleapis.com')
            if self.setup_model_monitoring:
                required_apis.append('logging.googleapis.com')
        return required_apis
