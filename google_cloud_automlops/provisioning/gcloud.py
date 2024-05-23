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

"""Creates GCloud infrastructure object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.provisioning.base import Infrastructure

from google_cloud_automlops.utils.utils import (
    render_jinja,
    write_and_chmod,
)

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GCLOUD_TEMPLATES_PATH,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_RESOURCES_SH_FILE,
    IAM_ROLES_RUNNER_SA,
)


class GCloud(Infrastructure):
    """Creates a GCloud specific Infrastructure object.

    Args:
        Infrastructure (object): Generic Infrastructure object.
    """

    def build(self):
        """Creates scripts/provision_resources.sh, which contains all GCloud commands needed to
        build the system's infrastructure.
        """
        write_and_chmod(
            GENERATED_RESOURCES_SH_FILE,
            render_jinja(
                template_path=import_files(GCLOUD_TEMPLATES_PATH) / 'provision_resources.sh.j2',
                artifact_repo_location=self.artifact_repo_location,
                artifact_repo_name=self.artifact_repo_name,
                artifact_repo_type=self.artifact_repo_type,
                base_dir=BASE_DIR,
                build_trigger_location=self.build_trigger_location,
                build_trigger_name=self.build_trigger_name,
                deployment_framework=self.deployment_framework,
                generated_license=GENERATED_LICENSE,
                generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
                naming_prefix=self.naming_prefix,
                pipeline_job_runner_service_account=self.pipeline_job_runner_service_account,
                pipeline_job_submission_service_location=self.pipeline_job_submission_service_location,
                pipeline_job_submission_service_name=self.pipeline_job_submission_service_name,
                pipeline_job_submission_service_type=self.pipeline_job_submission_service_type,
                project_id=self.project_id,
                pubsub_topic_name=self.pubsub_topic_name,
                required_apis=self.required_apis,
                required_iam_roles=IAM_ROLES_RUNNER_SA,
                schedule_location=self.schedule_location,
                schedule_name=self.schedule_name,
                schedule_pattern=self.schedule_pattern,
                source_repo_branch=self.source_repo_branch,
                source_repo_name=self.source_repo_name,
                source_repo_type=self.source_repo_type,
                storage_bucket_location=self.storage_bucket_location,
                storage_bucket_name=self.storage_bucket_name,
                use_ci=self.use_ci,
                vpc_connector=self.vpc_connector))
