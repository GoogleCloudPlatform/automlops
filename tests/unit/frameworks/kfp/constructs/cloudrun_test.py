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

"""Unit tests for cloudrun constructs kfp module."""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access

import pytest

from AutoMLOps.frameworks.kfp.constructs.cloudrun import KfpCloudRun
from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    LEFT_BRACKET,
    RIGHT_BRACKET
)
from AutoMLOps.utils.utils import write_yaml_file

# Create defaults file contents to test
DEFAULTS1 = {
    'gcp':
        {
            'af_registry_location': 'us-central1',
            'af_registry_name': 'vertex-mlops-af',
            'base_image': 'python:3.9-slim',
            'cb_trigger_location': 'us-central1',
            'cb_trigger_name': 'automlops-trigger',
            'cloud_run_location': 'us-central1',
            'cloud_run_name': 'run-pipeline',
            'cloud_tasks_queue_location': 'us-central1',
            'cloud_tasks_queue_name': 'queueing-svc',
            'cloud_schedule_location': 'us-central1',
            'cloud_schedule_name': 'AutoMLOps-schedule',
            'cloud_schedule_pattern': '0 */12 * * *',
            'cloud_source_repository': 'AutoMLOps-repo',
            'cloud_source_repository_branch': 'automlops',
            'gs_bucket_name': 'automlops-sandbox-bucket',
            'pipeline_runner_service_account': 'vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com',
            'project_id': 'automlops-sandbox',
            'vpc_connector': 'No VPC Specified'
        }
    }
DEFAULTS2 = {
    'gcp':
        {
            'af_registry_location': 'us-central1',
            'af_registry_name': 'vertex-mlops-af',
            'base_image': 'python:3.9-slim',
            'cb_trigger_location': 'us-central1',
            'cb_trigger_name': 'automlops-trigger',
            'cloud_run_location': 'us-central1',
            'cloud_run_name': 'run-pipeline',
            'cloud_tasks_queue_location': 'us-central1',
            'cloud_tasks_queue_name': 'queueing-svc',
            'cloud_schedule_location': 'us-central1',
            'cloud_schedule_name': 'AutoMLOps-schedule',
            'cloud_schedule_pattern': '0 */12 * * *',
            'cloud_source_repository': 'AutoMLOps-repo',
            'cloud_source_repository_branch': 'automlops',
            'gs_bucket_name': 'automlops-sandbox-bucket',
            'pipeline_runner_service_account': 'vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com',
            'project_id': 'automlops-sandbox',
            'vpc_connector': 'No VPC Specified'
        }
    }

@pytest.fixture(name='defaults_dict', params=[DEFAULTS1, DEFAULTS2])
def fixture_defaults_dict(request: pytest.FixtureRequest, tmpdir: pytest.FixtureRequest):
    """Writes temporary yaml file fixture using defaults parameterized
    dictionaries during pytest session scope.

    Args:
        request: Pytest fixture special object that provides information
            about the fixture.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """
    yaml_path = tmpdir.join('test.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}

def test_KfpCloudRun(defaults_dict: pytest.FixtureRequest):
    """Tests the KFP Cloud Run class.
    
    Args:
        defaults_dict: Locally defined defaults_dict Pytest fixture.
    """
    path = defaults_dict['path']
    defaults = defaults_dict['vals']
    my_cloudrun = KfpCloudRun(path)

    #Assert that created KfpCloudRun instance has the expected attribute values
    assert my_cloudrun._project_id == defaults['gcp']['project_id']
    assert my_cloudrun._pipeline_runner_service_account == defaults['gcp']['pipeline_runner_service_account']
    assert my_cloudrun._cloud_tasks_queue_location == defaults['gcp']['cloud_tasks_queue_location']
    assert my_cloudrun._cloud_tasks_queue_name == defaults['gcp']['cloud_tasks_queue_name']
    assert my_cloudrun._cloud_run_name == defaults['gcp']['cloud_run_name']
    assert my_cloudrun._cloud_run_location == defaults['gcp']['cloud_run_location']
    assert my_cloudrun._cloud_schedule_pattern == defaults['gcp']['cloud_schedule_pattern']
    assert my_cloudrun._cloud_schedule_location == defaults['gcp']['cloud_schedule_location']
    assert my_cloudrun._cloud_schedule_name == defaults['gcp']['cloud_schedule_name']

    assert my_cloudrun.dockerfile == (
        GENERATED_LICENSE +
        'FROM python:3.9-slim\n'
        '\n'
        '# Allow statements and log messages to immediately appear in the Knative logs\n'
        'ENV PYTHONUNBUFFERED True\n'
        '\n'
        '# Copy local code to the container image.\n'
        'ENV APP_HOME /app\n'
        'WORKDIR $APP_HOME\n'
        'COPY ./ ./\n'
        '\n'
        '# Upgrade pip\n'
        'RUN python -m pip install --upgrade pip\n'
        '# Install requirements\n'
        'RUN pip install --no-cache-dir -r /app/cloud_run/run_pipeline/requirements.txt\n'
        '# Compile pipeline spec\n'
        'RUN ./scripts/build_pipeline_spec.sh\n'
        '# Change Directories\n'
        'WORKDIR "/app/cloud_run/run_pipeline"\n'
        '# Run flask api server\n'
        'CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app\n'
    )

    assert my_cloudrun.cloudrun_base_reqs == (
        'kfp<2.0.0\n'
        'google-cloud-aiplatform\n'
        'google-cloud-pipeline-components\n'
        'Flask\n'
        'gunicorn\n'
        'pyyaml\n'
    )

    assert my_cloudrun.queueing_svc_reqs == (
        'google-cloud\n'
        'google-cloud-tasks\n'
        'google-api-python-client\n'
        'google-cloud-run\n'
        'google-cloud-scheduler\n'
    )

    assert my_cloudrun.cloudrun_base == (
        GENERATED_LICENSE +
        f'''"""Cloud Run to run pipeline spec"""\n'''
        f'''import logging\n'''
        f'''import os\n'''
        f'''from typing import Tuple\n'''
        f'\n'
        f'''import flask\n'''
        f'''from google.cloud import aiplatform\n'''
        f'''import yaml\n'''
        f'\n'
        f'''app = flask.Flask(__name__)\n'''
        f'\n'
        f'''logger = logging.getLogger()\n'''
        f'''log_level = os.environ.get('LOG_LEVEL', 'INFO')\n'''
        f'''logger.setLevel(log_level)\n'''
        f'\n'
        f'''CONFIG_FILE = '../../configs/defaults.yaml'\n'''
        f'''PIPELINE_SPEC_PATH_LOCAL = '../../scripts/pipeline_spec/pipeline_job.json'\n'''
        f'\n'
        f'''@app.route('/', methods=['POST'])\n'''
        f'''def process_request() -> flask.Response:\n'''
        f'''    """HTTP web service to trigger pipeline execution.\n'''
        f'\n'
        f'''    Returns:\n'''
        f'''        The response text, or any set of values that can be turned into a\n'''
        f'''        Response object using `make_response`\n'''
        f'''        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.\n'''
        f'''    """\n'''
        f'''    content_type = flask.request.headers['content-type']\n'''
        f'''    if content_type == 'application/json':\n'''
        f'''        request_json = flask.request.json\n'''
        f'\n'
        f'''        logging.debug('JSON Recieved:')\n'''
        f'''        logging.debug(request_json)\n'''
        f'\n'
        f'''        with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:\n'''
        f'''            config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
        f'\n'
        f'''        logging.debug('Calling run_pipeline()')\n'''
        f'''        dashboard_uri, resource_name = run_pipeline(\n'''
        f'''            project_id=config['gcp']['project_id'],\n'''
        f'''            pipeline_root=config['pipelines']['pipeline_storage_path'],\n'''
        f'''            pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],\n'''
        f'''            pipeline_params=request_json,\n'''
        f'''            pipeline_spec_path=PIPELINE_SPEC_PATH_LOCAL)\n'''
        f'''        return flask.make_response({LEFT_BRACKET}\n'''
        f'''            'dashboard_uri': dashboard_uri,\n'''
        f'''            'resource_name': resource_name\n'''
        f'''        {RIGHT_BRACKET}, 200)\n'''
        f'\n'
        f'''    else:\n'''
        f'''        raise ValueError(f'Unknown content type: {LEFT_BRACKET}content_type{RIGHT_BRACKET}')\n'''
        f'\n'
        f'''def run_pipeline(\n'''
        f'''    project_id: str,\n'''
        f'''    pipeline_root: str,\n'''
        f'''    pipeline_runner_sa: str,\n'''
        f'''    pipeline_params: dict,\n'''
        f'''    pipeline_spec_path: str,\n'''
        f'''    display_name: str = 'mlops-pipeline-run',\n'''
        f'''    enable_caching: bool = False) -> Tuple[str, str]:\n'''
        f'''    """Executes a pipeline run.\n'''
        f'\n'
        f'''    Args:\n'''
        f'''        project_id: The project_id.\n'''
        f'''        pipeline_root: GCS location of the pipeline runs metadata.\n'''
        f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
        f'''        pipeline_params: Pipeline parameters values.\n'''
        f'''        pipeline_spec_path: Location of the pipeline spec JSON.\n'''
        f'''        display_name: Name to call the pipeline.\n'''
        f'''        enable_caching: Should caching be enabled (Boolean)\n'''
        f'''    """\n'''
        f'''    logging.debug('Pipeline Parms Configured:')\n'''
        f'''    logging.debug(pipeline_params)\n'''
        f'\n'
        f'''    aiplatform.init(project=project_id)\n'''
        f'''    job = aiplatform.PipelineJob(\n'''
        f'''        display_name = display_name,\n'''
        f'''        template_path = pipeline_spec_path,\n'''
        f'''        pipeline_root = pipeline_root,\n'''
        f'''        parameter_values = pipeline_params,\n'''
        f'''        enable_caching = enable_caching)\n'''
        f'''    logging.debug('AI Platform job built. Submitting...')\n'''
        f'''    job.submit(service_account=pipeline_runner_sa)\n'''
        f'''    logging.debug('Job sent!')\n'''
        f'''    dashboard_uri = job._dashboard_uri()\n'''
        f'''    resource_name = job.resource_name\n'''
        f'''    return dashboard_uri, resource_name\n'''
        f'\n'
        f'''if __name__ == '__main__':\n'''
        f'''    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))\n'''
    )

    assert my_cloudrun.queueing_svc == (
        GENERATED_LICENSE +
        f'''"""Submit pipeline job using Cloud Tasks and create Cloud Scheduler Job."""\n'''
        f'''import argparse\n'''
        f'''import json\n'''
        f'\n'
        f'''from google.cloud import run_v2\n'''
        f'''from google.cloud import scheduler_v1\n'''
        f'''from google.cloud import tasks_v2\n'''
        f'\n'
        f'''CLOUD_RUN_LOCATION = '{defaults["gcp"]["cloud_run_location"]}'\n'''
        f'''CLOUD_RUN_NAME = '{defaults["gcp"]["cloud_run_name"]}'\n'''
        f'''CLOUD_TASKS_QUEUE_LOCATION = '{defaults["gcp"]["cloud_tasks_queue_location"]}'\n'''
        f'''CLOUD_TASKS_QUEUE_NAME = '{defaults["gcp"]["cloud_tasks_queue_name"]}'\n'''
        f'''PARAMETER_VALUES_PATH = 'queueing_svc/pipeline_parameter_values.json'\n'''
        f'''PIPELINE_RUNNER_SA = '{defaults["gcp"]["pipeline_runner_service_account"]}'\n'''
        f'''PROJECT_ID = '{defaults["gcp"]["project_id"]}'\n'''
        f'''SCHEDULE_LOCATION = '{defaults["gcp"]["cloud_schedule_location"]}'\n'''
        f'''SCHEDULE_PATTERN = '{defaults["gcp"]["cloud_schedule_pattern"]}'\n'''
        f'''SCHEDULE_NAME = '{defaults["gcp"]["cloud_schedule_name"]}'\n'''
        f'\n'
        f'''def get_runner_svc_uri(\n'''
        f'''    cloud_run_location: str,\n'''
        f'''    cloud_run_name: str,\n'''
        f'''    project_id: str):\n'''
        f'''    """Fetches the uri for the given cloud run instance.\n'''
        f'\n'
        f'''    Args:\n'''
        f'''        cloud_run_location: The location of the cloud runner service.\n'''
        f'''        cloud_run_name: The name of the cloud runner service.\n'''
        f'''        project_id: The project ID.\n'''
        f'''    Returns:\n'''
        f'''        str: Uri of the Cloud Run instance.\n'''
        f'''    """\n'''
        f'''    client = run_v2.ServicesClient()\n'''
        f'''    parent = client.service_path(project_id, cloud_run_location, cloud_run_name)\n'''
        f'''    request = run_v2.GetServiceRequest(name=parent)\n'''
        f'''    response = client.get_service(request=request)\n'''
        f'''    return response.uri\n'''
        f'\n'
        f'''def get_json_bytes(file_path: str):\n'''
        f'''    """Reads a json file at the specified path and returns as bytes.\n'''
        f'\n'
        f'''    Args:\n'''
        f'''        file_path: Path of the json file.\n'''
        f'''    Returns:\n'''
        f'''        bytes: Encode bytes of the file.\n'''
        f'''    """\n'''
        f'''    try:\n'''
        f'''        with open(file_path, 'r', encoding='utf-8') as file:\n'''
        f'''            data = json.load(file)\n'''
        f'''        file.close()\n'''
        f'''    except OSError as err:\n'''
        f'''        raise Exception(f'Error reading json file. {LEFT_BRACKET}err{RIGHT_BRACKET}') from err\n'''
        f'''    return json.dumps(data).encode()\n'''
        f'\n'
        f'''def create_cloud_task(\n'''
        f'''    cloud_tasks_queue_location: str,\n'''
        f'''    cloud_tasks_queue_name: str,\n'''
        f'''    parameter_values_path: str,\n'''
        f'''    pipeline_runner_sa: str,\n'''
        f'''    project_id: str,\n'''
        f'''    runner_svc_uri: str):\n'''
        f'''    """Create a task to the queue with the runtime parameters.\n'''
        f'\n'
        f'''    Args:\n'''
        f'''        cloud_run_location: The location of the cloud runner service.\n'''
        f'''        cloud_run_name: The name of the cloud runner service.\n'''
        f'''        cloud_tasks_queue_location: The location of the cloud tasks queue.\n'''
        f'''        cloud_tasks_queue_name: The name of the cloud tasks queue.\n'''
        f'''        parameter_values_path: Path to json pipeline params.\n'''
        f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
        f'''        project_id: The project ID.\n'''
        f'''        runner_svc_uri: Uri of the Cloud Run instance.\n'''
        f'''    """\n'''
        f'''    client = tasks_v2.CloudTasksClient()\n'''
        f'''    parent = client.queue_path(project_id, cloud_tasks_queue_location, cloud_tasks_queue_name)\n'''
        f'''    task = {LEFT_BRACKET}\n'''
        f'''        'http_request': {LEFT_BRACKET}\n'''
        f'''            'http_method': tasks_v2.HttpMethod.POST,\n'''
        f'''            'url': runner_svc_uri,\n'''
        f'''            'oidc_token': {LEFT_BRACKET}\n'''
        f'''                'service_account_email': pipeline_runner_sa,\n'''
        f'''                'audience': runner_svc_uri\n'''
        f'''            {RIGHT_BRACKET},\n'''
        f'''            'headers': {LEFT_BRACKET}\n'''
        f'''               'Content-Type': 'application/json'\n'''
        f'''            {RIGHT_BRACKET}\n'''
        f'''        {RIGHT_BRACKET}\n'''
        f'''    {RIGHT_BRACKET}\n'''
        f'''    task['http_request']['body'] = get_json_bytes(parameter_values_path)\n'''
        f'''    response = client.create_task(request={LEFT_BRACKET}'parent': parent, 'task': task{RIGHT_BRACKET})\n'''
        f'''    print(f'Created task {LEFT_BRACKET}response.name{RIGHT_BRACKET}')\n'''
        f'\n'
        f'''def create_cloud_scheduler_job(\n'''
        f'''    parameter_values_path: str,\n'''
        f'''    pipeline_runner_sa: str,\n'''
        f'''    project_id: str,\n'''
        f'''    runner_svc_uri: str,\n'''
        f'''    schedule_location: str,\n'''
        f'''    schedule_name: str,\n'''
        f'''    schedule_pattern: str):\n'''
        f'''    """Creates a scheduled pipeline job.\n'''
        f'\n'
        f'''    Args:\n'''
        f'''        parameter_values_path: Path to json pipeline params.\n'''
        f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
        f'''        project_id: The project ID.\n'''
        f'''        runner_svc_uri: Uri of the Cloud Run instance.\n'''
        f'''        schedule_location: The location of the scheduler resource.\n'''
        f'''        schedule_name: The name of the scheduler resource.\n'''
        f'''        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.\n'''
        f'''    """\n'''
        f'''    client = scheduler_v1.CloudSchedulerClient()\n'''
        f'''    parent = f'projects/{LEFT_BRACKET}project_id{RIGHT_BRACKET}/locations/{LEFT_BRACKET}schedule_location{RIGHT_BRACKET}'\n'''
        f'''    name = f'{LEFT_BRACKET}parent{RIGHT_BRACKET}/jobs/{LEFT_BRACKET}schedule_name{RIGHT_BRACKET}'\n'''
        f'\n'
        f'''    request = scheduler_v1.ListJobsRequest(parent=parent)\n'''
        f'''    page_result = client.list_jobs(request=request)\n'''
        f'''    for response in page_result:\n'''
        f'''        if response.name == name:\n'''
        f'''            print(f'Cloud Scheduler {LEFT_BRACKET}schedule_name{RIGHT_BRACKET} resource already exists in '\n'''
        f'''                  f'project {LEFT_BRACKET}project_id{RIGHT_BRACKET}.')\n'''
        f'''            return\n'''
        f'\n'
        f'''    oidc_token = scheduler_v1.OidcToken(\n'''
        f'''        service_account_email=pipeline_runner_sa,\n'''
        f'''        audience=runner_svc_uri)\n'''
        f'\n'
        f'''    target = scheduler_v1.HttpTarget(\n'''
        f'''       uri=runner_svc_uri,\n'''
        f'''        http_method=scheduler_v1.HttpMethod(1), # HTTP POST\n'''
        f'''        headers={LEFT_BRACKET}'Content-Type': 'application/json'{RIGHT_BRACKET},\n'''
        f'''        body=get_json_bytes(parameter_values_path),\n'''
        f'''        oidc_token=oidc_token)\n'''
        f'\n'
        f'''    job = scheduler_v1.Job(\n'''
        f'''       name=f'{LEFT_BRACKET}parent{RIGHT_BRACKET}/jobs/{LEFT_BRACKET}schedule_name{RIGHT_BRACKET}',\n'''
        f'''        description='AutoMLOps cloud scheduled run.',\n'''
        f'''        http_target=target,\n'''
        f'''        schedule=schedule_pattern)\n'''
        f'\n'
        f'''    request = scheduler_v1.CreateJobRequest(\n'''
        f'''        parent=parent,\n'''
        f'''        job=job)\n'''
        f'\n'
        f'''    response = client.create_job(request=request)\n'''
        f'''    print(response)\n'''
        f'\n'
        f'''if __name__ == '__main__':\n'''
        f'''    parser = argparse.ArgumentParser()\n'''
        f'''    parser.add_argument('--setting', type=str,\n'''
        f'''                       help='The config file for setting default values.')\n'''
        f'''    args = parser.parse_args()\n'''
        f'\n'
        f'''    uri = get_runner_svc_uri(\n'''
        f'''        cloud_run_location=CLOUD_RUN_LOCATION,\n'''
        f'''        cloud_run_name=CLOUD_RUN_NAME,\n'''
        f'''        project_id=PROJECT_ID)\n'''
        f'\n'
        f'''    if args.setting == 'queue_job':\n'''
        f'''        create_cloud_task(\n'''
        f'''            cloud_tasks_queue_location=CLOUD_TASKS_QUEUE_LOCATION,\n'''
        f'''            cloud_tasks_queue_name=CLOUD_TASKS_QUEUE_NAME,\n'''
        f'''            parameter_values_path=PARAMETER_VALUES_PATH,\n'''
        f'''            pipeline_runner_sa=PIPELINE_RUNNER_SA,\n'''
        f'''            project_id=PROJECT_ID,\n'''
        f'''            runner_svc_uri=uri)\n'''
        f'\n'
        f'''    if args.setting == 'schedule_job':\n'''
        f'''        create_cloud_scheduler_job(\n'''
        f'''            parameter_values_path=PARAMETER_VALUES_PATH,\n'''
        f'''            pipeline_runner_sa=PIPELINE_RUNNER_SA,\n'''
        f'''            project_id=PROJECT_ID,\n'''
        f'''            runner_svc_uri=uri,\n'''
        f'''            schedule_location=SCHEDULE_LOCATION,\n'''
        f'''            schedule_name=SCHEDULE_NAME,\n'''
        f'''            schedule_pattern=SCHEDULE_PATTERN)\n''')
