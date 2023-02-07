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
#
# DISCLAIMER: This code is generated as part of the AutoMLOps output.

"""Submit pipeline job using Cloud Tasks and create Cloud Scheduler Job."""
import argparse
import json

from google.cloud import run_v2
from google.cloud import scheduler_v1
from google.cloud import tasks_v2

CLOUD_RUN_LOCATION = 'us-central1'
CLOUD_RUN_NAME = 'run-pipeline'
CLOUD_TASKS_QUEUE_LOCATION = 'us-central1'
CLOUD_TASKS_QUEUE_NAME = 'queueing-svc'
PARAMETER_VALUES_PATH = 'queueing_svc/pipeline_parameter_values.json'
PIPELINE_RUNNER_SA = 'vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com'
PROJECT_ID = 'automlops-sandbox'
SCHEDULE_LOCATION = 'us-central1'
SCHEDULE_NAME = 'AutoMLOps-schedule'
SCHEDULE_PATTERN = '0 */12 * * *'

def get_runner_svc_uri(
    cloud_run_location: str,
    cloud_run_name: str,
    project_id: str):
    """Fetches the uri for the given cloud run instance.

    Args:
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        project_id: The project ID.
    Returns:
        str: Uri of the Cloud Run instance.
    """
    client = run_v2.ServicesClient()
    parent = client.service_path(project_id, cloud_run_location, cloud_run_name)
    request = run_v2.GetServiceRequest(name=parent)
    response = client.get_service(request=request)
    return response.uri

def get_json_bytes(file_path: str):
    """Reads a json file at the specified path and returns as bytes.

    Args:
        file_path: Path of the json file.
    Returns:
        bytes: Encode bytes of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        file.close()
    except OSError as err:
        raise Exception(f'Error reading json file. {err}') from err
    return json.dumps(data).encode()

def create_cloud_task(
    cloud_tasks_queue_location: str,
    cloud_tasks_queue_name: str,
    parameter_values_path: str,
    pipeline_runner_sa: str,
    project_id: str,
    runner_svc_uri: str):
    """Create a task to the queue with the runtime parameters.

    Args:
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        cloud_tasks_queue_location: The location of the cloud tasks queue.
        cloud_tasks_queue_name: The name of the cloud tasks queue.
        parameter_values_path: Path to json pipeline params.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        project_id: The project ID.
        runner_svc_uri: Uri of the Cloud Run instance.
    """
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project_id, cloud_tasks_queue_location, cloud_tasks_queue_name)
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': runner_svc_uri,
            'oidc_token': {
                'service_account_email': pipeline_runner_sa,
                'audience': runner_svc_uri
            },
            'headers': {
               'Content-Type': 'application/json'
            }
        }
    }
    task['http_request']['body'] = get_json_bytes(parameter_values_path)
    response = client.create_task(request={'parent': parent, 'task': task})
    print(f'Created task {response.name}')

def create_cloud_scheduler_job(
    parameter_values_path: str,
    pipeline_runner_sa: str,
    project_id: str,
    runner_svc_uri: str,
    schedule_location: str,
    schedule_name: str,
    schedule_pattern: str):
    """Creates a scheduled pipeline job.

    Args:
        parameter_values_path: Path to json pipeline params.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        project_id: The project ID.
        runner_svc_uri: Uri of the Cloud Run instance.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
    """
    client = scheduler_v1.CloudSchedulerClient()
    parent = f'projects/{project_id}/locations/{schedule_location}'
    name = f'{parent}/jobs/{schedule_name}'

    request = scheduler_v1.ListJobsRequest(parent=parent)
    page_result = client.list_jobs(request=request)
    for response in page_result:
        if response.name == name:
            print(f'Cloud Scheduler {schedule_name} resource already exists in '
                  f'project {project_id}.')
            return

    oidc_token = scheduler_v1.OidcToken(
        service_account_email=pipeline_runner_sa,
        audience=runner_svc_uri)

    target = scheduler_v1.HttpTarget(
       uri=runner_svc_uri,
        http_method=scheduler_v1.HttpMethod(1), # HTTP POST
        headers={'Content-Type': 'application/json'},
        body=get_json_bytes(parameter_values_path),
        oidc_token=oidc_token)

    job = scheduler_v1.Job(
       name=f'{parent}/jobs/{schedule_name}',
        description='AutoMLOps cloud scheduled run.',
        http_target=target,
        schedule=schedule_pattern)

    request = scheduler_v1.CreateJobRequest(
        parent=parent,
        job=job)

    response = client.create_job(request=request)
    print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--setting', type=str,
                       help='The config file for setting default values.')
    args = parser.parse_args()

    uri = get_runner_svc_uri(
        cloud_run_location=CLOUD_RUN_LOCATION,
        cloud_run_name=CLOUD_RUN_NAME,
        project_id=PROJECT_ID)

    if args.setting == 'queue_job':
        create_cloud_task(
            cloud_tasks_queue_location=CLOUD_TASKS_QUEUE_LOCATION,
            cloud_tasks_queue_name=CLOUD_TASKS_QUEUE_NAME,
            parameter_values_path=PARAMETER_VALUES_PATH,
            pipeline_runner_sa=PIPELINE_RUNNER_SA,
            project_id=PROJECT_ID,
            runner_svc_uri=uri)

    if args.setting == 'schedule_job':
        create_cloud_scheduler_job(
            parameter_values_path=PARAMETER_VALUES_PATH,
            pipeline_runner_sa=PIPELINE_RUNNER_SA,
            project_id=PROJECT_ID,
            runner_svc_uri=uri,
            schedule_location=SCHEDULE_LOCATION,
            schedule_name=SCHEDULE_NAME,
            schedule_pattern=SCHEDULE_PATTERN)
