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

"""Code strings for Cloudbuild scripts."""

# pylint: disable=line-too-long

from AutoMLOps.utils.constants import GENERATED_LICENSE

class CloudBuildScripts():
    """Generates CloudBuild yaml config file."""
    def __init__(self,
                 af_registry_location: str,
                 af_registry_name: str,
                 cloud_run_location: str,
                 cloud_run_name: str,
                 pipeline_runner_sa: str,
                 project_id: str,
                 run_local: str,
                 schedule_pattern: str,
                 base_dir: str,
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
            base_dir: Top directory name.
            vpc_connector: The name of the vpc connector to use.
        """

        # Set passed variables as hidden attributes
        self.__base_dir = base_dir
        self.__run_local = run_local

        # Parse defaults file for hidden class attributes
        self.__af_registry_name = af_registry_name
        self.__af_registry_location = af_registry_location
        self.__project_id = project_id
        self.__pipeline_runner_service_account = pipeline_runner_sa
        self.__vpc_connector = vpc_connector
        self.__cloud_run_name = cloud_run_name
        self.__cloud_run_location = cloud_run_location
        self.__cloud_schedule_pattern = schedule_pattern

        # Set generated scripts as public attributes
        self.create_kfp_cloudbuild_config = self._create_kfp_cloudbuild_config()

    def _create_kfp_cloudbuild_config(self):
        """Builds the content of cloudbuild.yaml.

        Args:
            str: Text content of cloudbuild.yaml.
        """
        vpc_connector_tail = ''
        if self.__vpc_connector != 'No VPC Specified':
            vpc_connector_tail = (
                f'\n'
                f'           "--ingress", "internal",\n'
                f'           "--vpc-connector", "{self.__vpc_connector}",\n'
                f'           "--vpc-egress", "all-traffic"')
        vpc_connector_tail += ']\n'

        cloudbuild_comp_config = (
            GENERATED_LICENSE +
            f'steps:\n'
            f'# ==============================================================================\n'
            f'# BUILD CUSTOM IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # build the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: [ "build", "-t", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest", "." ]\n'''
            f'''    dir: "{self.__base_dir}components/component_base"\n'''
            f'''    id: "build_component_base"\n'''
            f'''    waitFor: ["-"]\n''')

        cloudbuild_cloudrun_config = (
            f'\n'
            f'''  # build the run_pipeline image\n'''
            f'''  - name: 'gcr.io/cloud-builders/docker'\n'''
            f'''    args: [ "build", "-t", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest", "-f", "cloud_run/run_pipeline/Dockerfile", "." ]\n'''
            f'''    dir: "{self.__base_dir}"\n'''
            f'''    id: "build_pipeline_runner_svc"\n'''
            f'''    waitFor: ['build_component_base']\n'''
            f'\n'
            f'# ==============================================================================\n'
            f'# PUSH & DEPLOY CUSTOM IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # push the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest"]\n'''
            f'''    dir: "{self.__base_dir}components/component_base"\n'''
            f'''    id: "push_component_base"\n'''
            f'''    waitFor: ["build_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # push the run_pipeline image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest"]\n'''
            f'''    dir: "{self.__base_dir}"\n'''
            f'''    id: "push_pipeline_runner_svc"\n'''
            f'''    waitFor: ["push_component_base"]\n'''
            f'\n'
            f'''  # deploy the cloud run service\n'''
            f'''  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"\n'''
            f'''    entrypoint: gcloud\n'''
            f'''    args: ["run",\n'''
            f'''           "deploy",\n'''
            f'''           "{self.__cloud_run_name}",\n'''
            f'''           "--image",\n'''
            f'''           "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest",\n'''
            f'''           "--region",\n'''
            f'''           "{self.__cloud_run_location}",\n'''
            f'''           "--service-account",\n'''
            f'''           "{self.__pipeline_runner_service_account}",{vpc_connector_tail}'''
            f'''    id: "deploy_pipeline_runner_svc"\n'''
            f'''    waitFor: ["push_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # Copy runtime parameters\n'''
            f'''  - name: 'gcr.io/cloud-builders/gcloud'\n'''
            f'''    entrypoint: bash\n'''
            f'''    args:\n'''
            f'''      - '-e'\n'''
            f'''      - '-c'\n'''
            f'''      - |\n'''
            f'''        cp -r {self.__base_dir}cloud_run/queueing_svc .\n'''
            f'''    id: "setup_queueing_svc"\n'''
            f'''    waitFor: ["deploy_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # Install dependencies\n'''
            f'''  - name: python\n'''
            f'''    entrypoint: pip\n'''
            f'''    args: ["install", "-r", "queueing_svc/requirements.txt", "--user"]\n'''
            f'''    id: "install_queueing_svc_deps"\n'''
            f'''    waitFor: ["setup_queueing_svc"]\n'''
            f'\n'
            f'''  # Submit to queue\n'''
            f'''  - name: python\n'''
            f'''    entrypoint: python\n'''
            f'''    args: ["queueing_svc/main.py", "--setting", "queue_job"]\n'''
            f'''    id: "submit_job_to_queue"\n'''
            f'''    waitFor: ["install_queueing_svc_deps"]\n''')

        cloudbuild_scheduler_config = (
            '\n'
            '''  # Create Scheduler Job\n'''
            '''  - name: python\n'''
            '''    entrypoint: python\n'''
            '''    args: ["queueing_svc/main.py", "--setting", "schedule_job"]\n'''
            '''    id: "schedule_job"\n'''
            '''    waitFor: ["submit_job_to_queue"]\n''')

        custom_comp_image = (
            f'\n'
            f'images:\n'
            f'''  # custom component images\n'''
            f'''  - "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest"\n''')

        cloudrun_image = (
            f'''  # Cloud Run image\n'''
            f'''  - "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest"\n''')

        if self.__run_local:
            cb_file_contents = cloudbuild_comp_config + custom_comp_image
        else:
            if self.__cloud_schedule_pattern == 'No Schedule Specified':
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + custom_comp_image + cloudrun_image
            else:
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + cloudbuild_scheduler_config + custom_comp_image + cloudrun_image

        return cb_file_contents
