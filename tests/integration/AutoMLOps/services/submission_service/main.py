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

"""Submission service to submit pipeline spec to Vertex AI"""
import base64
import json
import logging
import os
from typing import Tuple

import flask
import functions_framework
from google.cloud import aiplatform
import google.cloud.logging


client = google.cloud.logging.Client(project="project")
client.setup_logging()

PROJECT_ID = 'airflow-sandbox-392816'
PIPELINE_ROOT = 'gs://airflow-sandbox-392816-dry-beans-dt-bucket/pipeline_root'
PIPELINE_JOB_RUNNER_SERVICE_ACCOUNT = 'vertex-pipelines@airflow-sandbox-392816.iam.gserviceaccount.com'

@functions_framework.http
def process_request(request: flask.Request) -> flask.Response:
    """HTTP web service to trigger pipeline execution.
    
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>

    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    
    content_type = request.headers['content-type']
    if content_type == 'application/json':
        request_json = request.get_json()
        try:
            base64_message = request_json['data']['data']
            data_payload = json.loads(base64.b64decode(base64_message).decode('utf-8'))
        except ValueError:
            logging.error('No data payload received, must receive runtime parameters.')
            return flask.make_response('Malformed request, received incorrect runtime parameters',
                                       400)

        logging.info('JSON Recieved:')
        logging.info(data_payload)

        if 'gs_pipeline_spec_path' in data_payload:
            gs_pipeline_spec_path = data_payload['gs_pipeline_spec_path']
            del data_payload['gs_pipeline_spec_path']
        else:
            logging.error('Pipeline spec path not found, must have path to pipeline spec file.')
            return flask.make_response('Malformed request, received incorrect runtime parameters. '
                                       'No pipeline spec path parameter found', 400)
        if 'vertex_experiment_tracking_name' in data_payload:
            vertex_exp = data_payload['vertex_experiment_tracking_name']
            del data_payload['vertex_experiment_tracking_name']
        else:
            vertex_exp = None

        logging.info('Calling submit_pipeline()')
        dashboard_uri, resource_name = submit_pipeline(
            project_id=PROJECT_ID,
            pipeline_root=PIPELINE_ROOT,
            pipeline_job_runner_service_account=PIPELINE_JOB_RUNNER_SERVICE_ACCOUNT,
            pipeline_params=data_payload,
            pipeline_spec_path=gs_pipeline_spec_path,
            experiment=vertex_exp)
        return flask.make_response({
            'dashboard_uri': dashboard_uri,
            'resource_name': resource_name
        }, 200)

    else:
        logging.error(f'Unknown content type: {content_type}')
        return flask.make_response('Non-json content_type received.', 400)

def submit_pipeline(
    project_id: str,
    pipeline_root: str,
    pipeline_job_runner_service_account: str,
    pipeline_params: dict,
    pipeline_spec_path: str,
    experiment: str,
    display_name: str = 'mlops-pipeline-run',
    enable_caching: bool = False) -> Tuple[str, str]:
    """Submits a pipeline run.

    Args:
        project_id: The project_id.
        pipeline_root: GCS location of the pipeline runs metadata.
        pipeline_job_runner_service_account: Service Account to runner PipelineJobs.
        pipeline_params: Pipeline parameters values.
        pipeline_spec_path: Location of the pipeline spec JSON.
        experiment: Optional name of Vertex AI experiment.
        display_name: Name to call the pipeline.
        enable_caching: Should caching be enabled (Boolean)
    """
    logging.info('Pipeline Parms Configured:')
    logging.info(pipeline_params)

    aiplatform.init(project=project_id)
    job = aiplatform.PipelineJob(
        display_name = display_name,
        template_path = pipeline_spec_path,
        pipeline_root = pipeline_root,
        parameter_values = pipeline_params,
        enable_caching = enable_caching)
    logging.info('AI Platform job built. Submitting...')
    job.submit(
        experiment=experiment,
        service_account=pipeline_job_runner_service_account)
    logging.info('Job sent!')
    dashboard_uri = job._dashboard_uri()
    resource_name = job.resource_name
    return dashboard_uri, resource_name
