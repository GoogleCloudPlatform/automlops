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

"""Model classes for AutoMLOps Provisioning Frameworks."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Optional

from pydantic import BaseModel

from google_cloud_automlops.provisioning.enums import PulumiRuntime


class PulumiConfig(BaseModel):
    """Model representing the pulumi config.

    Args:
        pipeline_model_name: Name of the model being deployed.
        region: region used in gcs infrastructure config.
        gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.
        artifact_repo_name: name of the artifact registry for the model infrastructure.
        source_repo_name: source repository used as part of the the model infra.
        cloudtasks_queue_name: name of the task queue used for model scheduling.
        cloud_build_trigger_name: name of the cloud build trigger for the model infra.
        provider: The provider option (default: Provider.TERRAFORM).
        pulumi_runtime: The pulumi runtime option (default: PulumiRuntime.PYTHON).
    """
    pipeline_model_name: str
    region: str
    gcs_bucket_name: str
    artifact_repo_name: str
    source_repo_name: str
    cloudtasks_queue_name: str
    cloud_build_trigger_name: str
    pulumi_runtime: PulumiRuntime = PulumiRuntime.PYTHON


class TerraformConfig(BaseModel):
    """Model representing the terraform config.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)
        build_trigger_location: The location of the build trigger (for cloud build).
        build_trigger_name: The name of the build trigger (for cloud build).
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        project_id: The project ID.
        provision_credentials_key: Either a path to or the contents of a service account key file in JSON format.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
    """
    artifact_repo_location: str
    artifact_repo_name: str
    artifact_repo_type: str
    build_trigger_location: str
    build_trigger_name: str
    deployment_framework: str
    naming_prefix: str
    pipeline_job_runner_service_account: str
    pipeline_job_submission_service_location: str
    pipeline_job_submission_service_name: str
    pipeline_job_submission_service_type: str
    provision_credentials_key: Optional[str]
    pubsub_topic_name: str
    schedule_location: str
    schedule_name: str
    schedule_pattern: str
    source_repo_branch: str
    source_repo_name: str
    source_repo_type: str
    storage_bucket_location: str
    storage_bucket_name: str
    use_ci: bool
    vpc_connector: str


class GcloudConfig(BaseModel):
    """Model representing the gcloud config.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)
        build_trigger_location: The location of the build trigger (for cloud build).
        build_trigger_name: The name of the build trigger (for cloud build).
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        project_id: The project ID.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
    """
    artifact_repo_location: str
    artifact_repo_name: str
    artifact_repo_type: str
    build_trigger_location: str
    build_trigger_name: str
    deployment_framework: str
    naming_prefix: str
    pipeline_job_runner_service_account: str
    pipeline_job_submission_service_location: str
    pipeline_job_submission_service_name: str
    pipeline_job_submission_service_type: str
    pubsub_topic_name: str
    schedule_location: str
    schedule_name: str
    schedule_pattern: str
    source_repo_branch: str
    source_repo_name: str
    source_repo_type: str
    storage_bucket_location: str
    storage_bucket_name: str
    use_ci: bool
    vpc_connector: str
