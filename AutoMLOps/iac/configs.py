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

"""Model classes for AutoMLOps."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from pydantic import BaseModel

from AutoMLOps.iac.enums import PulumiRuntime


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
        pipeline_model_name: Name of the model being deployed.
        region: region used in gcs infrastructure config.
        gcs_bucket_name: gcs bucket name to use as part of the model infrastructure.
        artifact_repo_name: name of the artifact registry for the model infrastructure.
        source_repo_name: source repository used as part of the the model infra.
        cloudtasks_queue_name: name of the task queue used for model scheduling.
        cloud_build_trigger_name: name of the cloud build trigger for the model infra.
        provider: The provider option (default: Provider.TERRAFORM).
        workspace_name: Name of the terraform cloud workspace.
        creds_tf_var_name: Name of tf variable with project access credentials json key.
    """
    pipeline_model_name: str
    creds_tf_var_name: str
    workspace_name: str
    region: str
    gcs_bucket_name: str
    artifact_repo_name: str
    cloudtasks_queue_name: str
    cloud_build_trigger_name: str
    source_repo_name: str
