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

"""Builds pipeline files."""

import json

from . import BuilderUtils

# pylint: disable=line-too-long
def formalize(pipeline_parameter_values: dict,
              parameter_values_path: str,
              top_lvl_name: str):
    """Constructs and writes pipeline.py, pipeline_runner.py, and pipeline_parameter_values.json files.
        pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.

    Args:
        pipeline_parameter_values: Dictionary of runtime parameters for the PipelineJob.
        parameter_values_path: File to write the pipeline parameter values.
        top_lvl_name: Top directory name.
    Raises:
        Exception: If an error is encountered reading/writing to a file.
    """
    pipeline_file = top_lvl_name + 'pipelines/pipeline.py'
    pipeline_runner_file = top_lvl_name + 'pipelines/pipeline_runner.py'
    pipeline_params_file = top_lvl_name + parameter_values_path
    # construct pipeline.py
    pipeline_imports = get_pipeline_imports()
    pipeline_argparse = get_pipeline_argparse()
    try:
        with open(pipeline_file, 'r+', encoding='utf-8') as file:
            pipeline_scaffold = file.read()
            file.seek(0, 0)
            file.write(BuilderUtils.LICENSE)
            file.write(pipeline_imports)
            for line in pipeline_scaffold.splitlines():
                file.write('    ' + line + '\n')
            file.write(pipeline_argparse)
        file.close()
    except OSError as err:
        raise Exception(f'Error interacting with file. {err}') from err
    # construct pipeline_runner.py
    BuilderUtils.write_file(pipeline_runner_file, get_pipeline_runner(), 'w+')
    # construct pipeline_parameter_values.json
    serialized_params = json.dumps(pipeline_parameter_values, indent=4)
    BuilderUtils.write_file(pipeline_params_file, serialized_params, 'w+')

def get_pipeline_imports() -> str:
    """Generates python code that imports modules and loads all custom components.

    Returns:
        str: Python pipeline_imports code.
    """
    components_list = BuilderUtils.get_components_list(full_path=False)
    quote = '\''
    newline_tab = '\n    '
    return (
        f'''import os\n'''
        f'''import argparse\n'''
        f'''import yaml\n'''
        f'''import kfp\n'''
        f'''from kfp.v2 import compiler, dsl\n'''
        f'''from kfp.v2.dsl import pipeline, component, Artifact, Dataset, Input, Metrics, Model, Output, InputPath, OutputPath\n'''
        f'''from kfp.v2.compiler import compiler\n'''
        f'\n'
        f'''def load_custom_component(component_name: str):\n'''
        f'''    component_path = os.path.join('components',\n'''
        f'''                                component_name,\n'''
        f'''                              'component.yaml')\n'''
        f'''    return kfp.components.load_component_from_file(component_path)\n'''
        f'\n'
        f'''def create_training_pipeline(pipeline_job_spec_path: str):\n'''
        f'''    {newline_tab.join(f'{component} = load_custom_component(component_name={quote}{component}{quote})' for component in components_list)}'''
        f'\n')

def get_pipeline_argparse() -> str:
    """Generates python code that loads default pipeline parameters from the defaults config_file.

    Returns:
        str: Python pipeline_argparse code.
    """
    return (
        '''    compiler.Compiler().compile(\n'''
        '''        pipeline_func=pipeline,\n'''
        '''        package_path=pipeline_job_spec_path)\n'''
        '\n'
        '''if __name__ == '__main__':\n'''
        '''    parser = argparse.ArgumentParser()\n'''
        '''    parser.add_argument('--config', type=str,\n'''
        '''                       help='The config file for setting default values.')\n'''
        '\n'
        '''    args = parser.parse_args()\n'''
        '\n'
        '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
        '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
        '\n'
        '''    pipeline = create_training_pipeline(\n'''
        '''        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])\n''')

def get_pipeline_runner() -> str:
    """Generates python code that sends a PipelineJob to Vertex AI.

    Returns:
        str: Python pipeline_runner code.
    """
    return (BuilderUtils.LICENSE +
        '''import argparse\n'''
        '''import json\n'''
        '''import os\n'''
        '''import yaml\n'''
        '''import logging\n'''
        '\n'
        '''from google.cloud import aiplatform\n'''
        '\n'
        '''logger = logging.getLogger()\n'''
        '''log_level = os.environ.get('LOG_LEVEL', 'INFO')\n'''
        '''logger.setLevel(log_level)\n'''
        '\n'
        '''def run_pipeline(\n'''
        '''    project_id: str,\n'''
        '''    pipeline_root: str,\n'''
        '''    pipeline_runner_sa: str,\n'''
        '''    parameter_values_path: str,\n'''
        '''    pipeline_spec_path: str,\n'''
        '''    display_name: str = 'mlops-pipeline-run',\n'''
        '''    enable_caching: bool = False):\n'''
        '''    """Executes a pipeline run.\n'''
        '\n'
        '''    Args:\n'''
        '''        project_id: The project_id.\n'''
        '''        pipeline_root: GCS location of the pipeline runs metadata.\n'''
        '''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
        '''        parameter_values_path: Location of parameter values JSON.\n'''
        '''        pipeline_spec_path: Location of the pipeline spec JSON.\n'''
        '''        display_name: Name to call the pipeline.\n'''
        '''        enable_caching: Should caching be enabled (Boolean)\n'''
        '''    """\n'''
        '''    with open(parameter_values_path, 'r') as file:\n'''
        '''        try:\n'''
        '''            pipeline_params = json.load(file)\n'''
        '''        except ValueError as exc:\n'''
        '''            print(exc)\n'''
        '''    logging.debug('Pipeline Parms Configured:')\n'''
        '''    logging.debug(pipeline_params)\n'''
        '\n'
        '''    aiplatform.init(project=project_id)\n'''
        '''    job = aiplatform.PipelineJob(\n'''
        '''        display_name = display_name,\n'''
        '''        template_path = pipeline_spec_path,\n'''
        '''        pipeline_root = pipeline_root,\n'''
        '''        parameter_values = pipeline_params,\n'''
        '''        enable_caching = enable_caching)\n'''
        '''    logging.debug('AI Platform job built. Submitting...')\n'''
        '''    job.submit(service_account=pipeline_runner_sa)\n'''
        '''    logging.debug('Job sent!')\n'''
        '\n'
        '''if __name__ == '__main__':\n'''
        '''    parser = argparse.ArgumentParser()\n'''
        '''    parser.add_argument('--config', type=str,\n'''
        '''                        help='The config file for setting default values.')\n'''
        '''    args = parser.parse_args()\n'''
        '\n'
        '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
        '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
        '\n'
        '''    run_pipeline(project_id=config['gcp']['project_id'],\n'''
        '''                 pipeline_root=config['pipelines']['pipeline_storage_path'],\n'''
        '''                 pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],\n'''
        '''                 parameter_values_path=config['pipelines']['parameter_values_path'],\n'''
        '''                 pipeline_spec_path=config['pipelines']['pipeline_job_spec_path']) \n''')

def create_pipeline_scaffold(name: str,
                             params: list,
                             pipeline: list,
                             description: str = None):
    """Creates a temporary pipeline scaffold which will
       be used by the formalize function.

    Args:
        name: Pipeline name.
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        pipeline: Defines the components to use in the pipeline,
            their order, and a mapping of component params to
            pipeline params. A list of dictionaries, each dict
            specifies a custom component and contains keys:
                'component_name': name of the component
                'param_mapping': a list of tuples mapping ->
                    (component_param, pipeline_param)
        description: Optional description of the pipeline.
    """
    BuilderUtils.validate_name(name)
    BuilderUtils.validate_params(params)
    BuilderUtils.validate_pipeline_structure(pipeline)
    BuilderUtils.make_dirs([BuilderUtils.TMPFILES_DIR]) # if it doesn't already exist
    pipeline_scaffold = get_pipeline_scaffold(name, params, pipeline, description)
    BuilderUtils.write_file(BuilderUtils.PIPELINE_TMPFILE, pipeline_scaffold, 'w')

def get_pipeline_scaffold(name: str,
                          params: list,
                          pipeline: list,
                          description: str):
    """Generates the Kubeflow pipeline definition. Uses a
       queue to define .after() ordering in the pipeline.

    Args:
        name: Pipeline name.
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        pipeline: Defines the components to use in the pipeline,
            their order, and a mapping of component params to
            pipeline params. A list of dictionaries, each dict
            specifies a custom component and contains keys:
                'component_name': name of the component
                'param_mapping': a list of tuples mapping ->
                    (component_param, pipeline_param)
        description: Optional description of the pipeline.
    """
    newline = '\n'
    queue = ['']
    for idx, component in enumerate(pipeline):
        if idx != len(pipeline)-1:
            queue.append(f'''.after({component['component_name']}_task)''')
    return (
        f'\n'
        f'@dsl.pipeline(\n'
        f'''    name='{name}',\n'''
        f'''    description='{description}')\n'''
        f'def pipeline(\n'
        f'''{newline.join(f"    {param['name']}: {param['type'].__name__}," for param in params)}\n'''
        f'):\n'
        f'''    """{description}\n'''
        f'\n'
        f'    Args:\n'
        f'''{newline.join(f"        {param['name']}: {param['description']}," for param in params)}\n'''
        f'    """\n'
        f"""{newline.join(
        f'''    {component['component_name']}_task = {component['component_name']}({newline}'''
        f'''    {f'{newline}    '.join(f"   {param[0]}={param[1]}," for param in component['param_mapping'])}{newline}'''
        f'''    ){queue.pop(0)}{newline}'''
        for component in pipeline
        )}"""
        f'\n'
    )
