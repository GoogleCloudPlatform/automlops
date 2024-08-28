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

"""Creates enums for orchestrator and submission service options
as well as generic component, pipeline, and services objects."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from enum import Enum
from pydantic import BaseModel, validator


class Deployer(Enum):
    """Enum representing the available options for orchestration management."""

    CLOUDBUILD = 'cloud-build'
    GITHUB_ACTIONS = 'github-actions'
    # GITLAB_CI = 'gitlab-ci'   # roadmap item
    # JENKINS = 'jenkins'   # roadmap item


class Provisioner(Enum):
    """Enum representing the available providers for infrastructure management."""

    TERRAFORM = 'terraform'
    # PULUMI = 'pulumi' roadmap item
    GCLOUD = 'gcloud'


class Orchestrator(Enum):
    """Enum representing the available options for orchestration management."""

    KFP = 'kfp'
    # ARGO_WORKFLOWS = 'argo-workflows'   # roadmap item
    # TFX = 'tfx'   # roadmap item
    # AIRFLOW = 'airflow'   # roadmap item
    # RAY = 'ray'   # roadmap item


class ArtifactRepository(Enum):
    """Enum representing the available options for artifact repositories."""

    ARTIFACT_REGISTRY = 'artifact-registry'


class CodeRepository(Enum):
    """Enum representing the available options for source code repositories."""

    # BITBUCKET = 'bitbucket'   # roadmap item
    CLOUD_SOURCE_REPOSITORIES = 'cloud-source-repositories'
    # GITHUB = 'github'
    # GITLAB = 'gitlab'   # roadmap item


class PipelineJobSubmitter(Enum):
    """Enum representing the available options for the Pipeline Job submission service."""

    CLOUD_FUNCTIONS = 'cloud-functions'
    CLOUD_RUN = 'cloud-run'


class PulumiRuntime(Enum):
    """Enum representing the available pulumi runtimes."""

    PYTHON = 'python'
    TYPESCRIPT = 'typescript'
    GO = 'go'


class GCPLocations(Enum):
    """Enum representing the available GCP locations.
    """
    US_CENTRAL_1 = 'us-central1'
    US_EAST_1 = 'us-east1'
    US_EAST_4 = 'us-east4'
    US_EAST_5 = 'us-east5'
    US_WEST_1 = 'us-west1'
    US_WEST_2 = 'us-west2'
    US_WEST_3 = 'us-west3'
    US_WEST_4 = 'us-west4'
    US_SOUTH_1 = 'us-south1'


class Parameter(BaseModel):
    name: str
    type: type
    description: str

    @validator("type", pre=True)
    def type_to_empty(cls, v: object) -> object:
        if v is None:
            return ""
        return v
    @validator("description", pre=True)
    def description_to_empty(cls, v: object) -> object:
        if v is None:
            return ""
        return v


class GCP(BaseModel):
    """Class representing all GCP configuration settings.
    """
    artifact_repo_location: GCPLocations
    artifact_repo_name: str
    artifact_repo_type: str
    base_image: str
    build_trigger_location: str
    build_trigger_name: str
    naming_prefix: str
    pipeline_job_runner_service_account: str
    pipeline_job_submission_service_location: str
    pipeline_job_submission_service_name: str
    pipeline_job_submission_service_type: str
    project_id: str
    setup_model_monitoring: bool
    pubsub_topic_name: str
    schedule_location: str
    schedule_name: str
    schedule_pattern: str
    source_repository_branch: str
    source_repository_name: str
    source_repository_type: str
    storage_bucket_location: str
    storage_bucket_name: str
    vpc_connector: str


class PipelineSpecs(BaseModel):
    gs_pipeline_job_spec_path: str
    parameter_values_path: str
    pipeline_component_directory: str
    pipeline_job_spec_path: str
    pipeline_region: str
    pipeline_storage_path: str


class Tooling(BaseModel):
    deployment_framework: Deployer
    provisioning_framework: Provisioner
    orchestration_framework: Orchestrator
    use_ci: bool


class Defaults(BaseModel):
    gcp: GCP
    pipeline_specs: PipelineSpecs
    tooling: Tooling
