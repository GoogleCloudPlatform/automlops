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

from AutoMLOps.utils.utils import write_file
from AutoMLOps.utils.constants import (
    BASE_DIR,
    GENERATED_CLOUDBUILD_FILE
)
from AutoMLOps.deployments.cloudbuild.constructs.scripts import CloudBuildScripts

def build(af_registry_location: str,
          af_registry_name: str,
          cloud_run_location: str,
          cloud_run_name: str,
          pipeline_runner_sa: str,
          project_id: str,
          run_local: bool,
          schedule_pattern: str,
          vpc_connector: str):
    """Constructs scripts for resource deployment and running Kubeflow pipelines.

    Args:
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        project_id: The project ID.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        vpc_connector: The name of the vpc connector to use.
    """
    # Get scripts builder object
    cb_scripts = CloudBuildScripts(
        af_registry_location, af_registry_name, cloud_run_location,
        cloud_run_name, pipeline_runner_sa, project_id,
        run_local, schedule_pattern, BASE_DIR,
        vpc_connector)

    # Write cloud build config
    write_file(GENERATED_CLOUDBUILD_FILE, cb_scripts.create_kfp_cloudbuild_config, 'w+')
