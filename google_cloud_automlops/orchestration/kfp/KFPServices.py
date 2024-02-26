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

"""Creates a KFP services subclass."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.orchestration.Services import Services
from google_cloud_automlops.utils.utils import (
    read_yaml_file,
    render_jinja,
    write_file
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_DEFAULTS_FILE,
    GENERATED_LICENSE,
    KFP_TEMPLATES_PATH,
    PINNED_KFP_VERSION
)


class KFPServices(Services):
    """Creates a KFP specific Services object for #TODO: add more

    Args:
        Services (object): Generic Services object.
    """

    def __init__(self) -> None:
        """Initializes KFPServices Object.
        """

    def _build_dockerfile(self):
        """Writes the services/submission_service/Dockerfile #TODO add more
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

        write_file(
            f'{self.submission_service_base_dir}/Dockerfile', 
            render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'Dockerfile.j2',
                base_dir=BASE_DIR,
                generated_license=GENERATED_LICENSE),
            'w')

    def _build_requirements(self):
        """Writes the services/submission_service/requirements.txt #TODO add more
        """
        write_file(
            f'{self.submission_service_base_dir}/requirements.txt', 
            render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'requirements.txt.j2',
                pinned_kfp_version=PINNED_KFP_VERSION,
                pipeline_job_submission_service_type=self.pipeline_job_submission_service_type),
            'w')

    def _build_main(self):
        """Writes the services/submission_service/main.py file to #TODO add more
        """
        write_file(
            f'{self.submission_service_base_dir}/main.py', 
            render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'main.py.j2',
                generated_license=GENERATED_LICENSE,
                pipeline_root=self.pipeline_storage_path,
                pipeline_job_runner_service_account=self.pipeline_job_runner_service_account,
                pipeline_job_submission_service_type=self.pipeline_job_submission_service_type,
                project_id=self.project_id),
            'w')
