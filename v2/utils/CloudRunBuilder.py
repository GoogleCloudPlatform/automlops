"""Builds cloud_run files."""
from . import BuilderUtils

# pylint: disable=line-too-long
def formalize(top_lvl_name: str):
    """Constructs and writes a Dockerfile, requirements.txt, and
       main.py to the cloud_run/run_pipeline directory.

    Args:
        top_lvl_name: Top directory name.
    """
    cloudrun_base = top_lvl_name + 'cloud_run/run_pipeline'
    BuilderUtils.make_dirs([top_lvl_name + 'cloud_run', cloudrun_base])
    create_dockerfile(cloudrun_base)
    create_requirements(cloudrun_base)
    create_main(cloudrun_base)

def create_dockerfile(cloudrun_base: str):
    """Writes a Dockerfile to the cloud_run/run_pipeline directory.

    Args:
        cloudrun_base: Base dir for cloud_run files.
    """
    dockerfile = (
        'FROM python:3.9\n'
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
    BuilderUtils.write_file(f'{cloudrun_base}/Dockerfile', dockerfile, 'w')

def create_requirements(cloudrun_base: str):
    """Writes a requirements.txt to the cloud_run/run_pipeline
       directory.

    Args:
        cloudrun_base: Base dir for cloud_run files.
    """
    requirements = (
        'kfp\n'
        'google-cloud-aiplatform\n'
        'Flask\n'
        'gunicorn\n'
        'pyyaml\n'
    )
    BuilderUtils.write_file(f'{cloudrun_base}/requirements.txt', requirements, 'w')

def create_main(cloudrun_base: str):
    """Writes main.py to the cloud_run/run_pipeline
       directory. This file contains code for running
       a flask service that will act as a pipeline
       runner service.

    Args:
        cloudrun_base: Base dir for cloud_run files.
    """
    left_bracket = '{'
    right_bracket = '}'
    code = (
        f'"""Cloud Run to run pipeline spec"""\n'''
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
        f'''        return flask.make_response({left_bracket}\n'''
        f'''            'dashboard_uri': dashboard_uri,\n'''
        f'''            'resource_name': resource_name\n'''
        f'''        {right_bracket}, 200)\n'''
        f'\n'
        f'''    else:\n'''
        f'''        raise ValueError(f'Unknown content type: {left_bracket}content_type{right_bracket}')\n'''
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
        f'''    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))\n''')
    BuilderUtils.write_file(f'{cloudrun_base}/main.py', code, 'w')
