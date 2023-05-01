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

"""Cloud Run to run pipeline spec"""
import logging
import os
from typing import Tuple

import flask
from google.cloud import aiplatform
import yaml

app = flask.Flask(__name__)

logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

CONFIG_FILE = '../../configs/defaults.yaml'
PIPELINE_SPEC_PATH_LOCAL = '../../scripts/pipeline_spec/pipeline_job.json'

@app.route('/', methods=['POST'])
def process_request() -> flask.Response:
    """HTTP web service to trigger pipeline execution.

    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    content_type = flask.request.headers['content-type']
    if content_type == 'application/json':
        request_json = flask.request.json

        logging.debug('JSON Recieved:')
        logging.debug(request_json)

        with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)

        logging.debug('Calling run_pipeline()')
        dashboard_uri, resource_name = run_pipeline(
            project_id=config['gcp']['project_id'],
            pipeline_root=config['pipelines']['pipeline_storage_path'],
            pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],
            pipeline_params=request_json,
            pipeline_spec_path=PIPELINE_SPEC_PATH_LOCAL)
        return flask.make_response({
            'dashboard_uri': dashboard_uri,
            'resource_name': resource_name
        }, 200)

    else:
        raise ValueError(f'Unknown content type: {content_type}')

def run_pipeline(
    project_id: str,
    pipeline_root: str,
    pipeline_runner_sa: str,
    pipeline_params: dict,
    pipeline_spec_path: str,
    display_name: str = 'mlops-pipeline-run',
    enable_caching: bool = False) -> Tuple[str, str]:
    """Executes a pipeline run.

    Args:
        project_id: The project_id.
        pipeline_root: GCS location of the pipeline runs metadata.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        pipeline_params: Pipeline parameters values.
        pipeline_spec_path: Location of the pipeline spec JSON.
        display_name: Name to call the pipeline.
        enable_caching: Should caching be enabled (Boolean)
    """
    logging.debug('Pipeline Parms Configured:')
    logging.debug(pipeline_params)

    aiplatform.init(project=project_id)
    job = aiplatform.PipelineJob(
        display_name = display_name,
        template_path = pipeline_spec_path,
        pipeline_root = pipeline_root,
        parameter_values = pipeline_params,
        enable_caching = enable_caching)
    logging.debug('AI Platform job built. Submitting...')
    job.submit(service_account=pipeline_runner_sa)
    logging.debug('Job sent!')
    dashboard_uri = job._dashboard_uri()
    resource_name = job.resource_name
    return dashboard_uri, resource_name

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
