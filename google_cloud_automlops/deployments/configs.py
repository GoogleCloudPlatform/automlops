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

"""Model classes for AutoMLOps Orchestration Frameworks."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from pydantic import BaseModel


class CloudBuildConfig(BaseModel):
    """Model representing the Cloud Build config.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        project_id: The project ID.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        use_ci: Flag that determines whether to use Cloud CI/CD.
    """
    artifact_repo_location: str
    artifact_repo_name: str
    naming_prefix: str
    project_id: str
    pubsub_topic_name: str
    use_ci: bool

class GitHubActionsConfig(BaseModel):
    """Model representing the GitHub Actions config.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        project_id: The project ID.
        project_number: The project number.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        source_repo_branch: The branch to use in the source repository.
        use_ci: Flag that determines whether to use Cloud CI/CD.
        workload_identity_pool: Pool for workload identity federation. 
        workload_identity_provider: Provider for workload identity federation.
        workload_identity_service_account: Service account for workload identity federation. 
    """
    artifact_repo_location: str
    artifact_repo_name: str
    naming_prefix: str
    project_id: str
    project_number: str #TODO: Check if there's any other way to pass this, could use a util with the GCP client library. See https://github.com/GoogleCloudPlatform/java-docs-samples/blob/main/content-warehouse/src/main/java/contentwarehouse/v1/CreateDocument.java#L125-L135
    pubsub_topic_name: str
    source_repo_branch: str
    use_ci: bool
    workload_identity_pool: str
    workload_identity_provider: str
    workload_identity_service_account: str
    