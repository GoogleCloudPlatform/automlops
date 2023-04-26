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

# pylint: disable=C0103
# pylint: disable=line-too-long

import json
from typing import Callable, Dict, List, Optional

from AutoMLOps import BuilderUtils

DEFAULT_PIPELINE_NAME = 'automlops-pipeline'

def formalize(custom_training_job_specs: List[Dict],
              defaults_file: str,
              pipeline_parameter_values: dict,
              top_lvl_name: str):
    """Constructs and writes pipeline.py, pipeline_runner.py, and pipeline_parameter_values.json files.
        pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.

    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        defaults_file: Path to the default config variables yaml.
        pipeline_parameter_values: Dictionary of runtime parameters for the PipelineJob.
        top_lvl_name: Top directory name.
    Raises:
        Exception: If an error is encountered reading/writing to a file.
    """
    defaults = BuilderUtils.read_yaml_file(defaults_file)
    pipeline_file = top_lvl_name + 'pipelines/pipeline.py'
    pipeline_runner_file = top_lvl_name + 'pipelines/pipeline_runner.py'
    pipeline_params_file = top_lvl_name + BuilderUtils.PARAMETER_VALUES_PATH
    # construct pipeline.py
    pipeline_imports = get_pipeline_imports(custom_training_job_specs, defaults['gcp']['project_id'])
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
        raise OSError(f'Error interacting with file. {err}') from err
    # construct pipeline_runner.py
    BuilderUtils.write_file(pipeline_runner_file, get_pipeline_runner(), 'w+')
    # construct pipeline_parameter_values.json
    serialized_params = json.dumps(pipeline_parameter_values, indent=4)
    BuilderUtils.write_file(pipeline_params_file, serialized_params, 'w+')

def get_pipeline_imports(custom_training_job_specs: List[Dict], project_id: str) -> str:
    """Generates python code that imports modules and loads all custom components.
    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        project_id: The project_id to run the pipeline. 

    Returns:
        str: Python pipeline_imports code.
    """
    components_list = BuilderUtils.get_components_list(full_path=False)
    gcpc_imports = (
        'from functools import partial\n'
        'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component\n')
    quote = '\''
    newline_tab = '\n    '
    return (
        f'''import argparse\n'''
        f'''import os\n'''
        f'''{gcpc_imports if custom_training_job_specs else ''}'''
        f'''import kfp\n'''
        f'''from kfp.v2 import compiler, dsl\n'''
        f'''from kfp.v2.dsl import *\n'''
        f'''from typing import *\n'''
        f'''import yaml\n'''
        f'\n'
        f'''def load_custom_component(component_name: str):\n'''
        f'''    component_path = os.path.join('components',\n'''
        f'''                                component_name,\n'''
        f'''                              'component.yaml')\n'''
        f'''    return kfp.components.load_component_from_file(component_path)\n'''
        f'\n'
        f'''def create_training_pipeline(pipeline_job_spec_path: str):\n'''
        f'''    {newline_tab.join(f'{component} = load_custom_component(component_name={quote}{component}{quote})' for component in components_list)}\n'''
        f'\n'
        f'''{get_custom_job_specs(custom_training_job_specs, project_id)}''')

def get_custom_job_specs(custom_training_job_specs: List[Dict], project_id: str) -> str:
    """Generates python code that creates a custom training op from the specified component.
    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        project_id: The project_id to run the pipeline. 

    Returns:
        str: Python custom training op code.
    """
    quote = '\''
    newline_tab = '\n    '
    output_string = '' if not custom_training_job_specs else (
            f'''    {newline_tab.join(f'{spec["component_spec"]}_custom_training_job_specs = {format_spec_dict(spec)}' for spec in custom_training_job_specs)}'''
            f'\n'
            f'''    {newline_tab.join(f'{spec["component_spec"]}_job_op = create_custom_training_job_op_from_component(**{spec["component_spec"]}_custom_training_job_specs)' for spec in custom_training_job_specs)}'''
            f'\n'
            f'''    {newline_tab.join(f'{spec["component_spec"]} = partial({spec["component_spec"]}_job_op, project={quote}{project_id}{quote})' for spec in custom_training_job_specs)}'''        
            f'\n')
    return output_string

def format_spec_dict(job_spec: dict) -> str:
    """Takes in a job spec dictionary and removes the quotes around the component op name. 
       e.g. 'component_spec': 'train_model' becomes 'component_spec': train_model.
       This is necessary to in order for the op to be callable within the Python code.

    Args:
        job_spec: Dictionary with job spec info.

    Returns:
        str: Python formatted dictionary code.
    """
    quote = '\''
    left_bracket = '{'
    right_bracket = '}'
    newline = '\n'

    return (
        f'''{left_bracket}\n'''
        f'''    {f'{newline}    '.join(f"   {quote}{k}{quote}: {quote if k != 'component_spec' else ''}{v}{quote if k != 'component_spec' else ''}," for k, v in job_spec.items())}{newline}'''
        f'''    {right_bracket}\n''')

def get_pipeline_argparse() -> str:
    """Generates python code that loads default pipeline parameters from the defaults config_file.

    Returns:
        str: Python pipeline_argparse code.
    """
    return (
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
        '''import logging\n'''
        '''import os\n'''
        '''import yaml\n'''
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

def create_pipeline_scaffold(func: Optional[Callable] = None,
                             *,
                             name: Optional[str] = None,
                             description: Optional[str] = None):
    """Creates a temporary pipeline scaffold which will
       be used by the formalize function.

    Args:
        func: The python function to create a pipeline from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
    """
    pipeline_scaffold = (get_pipeline_decorator(name, description) +
                         BuilderUtils.get_function_source_definition(func) +
                         get_compile_step(func.__name__))
    BuilderUtils.make_dirs([BuilderUtils.TMPFILES_DIR]) # if it doesn't already exist
    BuilderUtils.write_file(BuilderUtils.PIPELINE_TMPFILE, pipeline_scaffold, 'w')

def get_pipeline_decorator(name: Optional[str] = None,
                           description: Optional[str] = None):
    default_name = DEFAULT_PIPELINE_NAME if not name else name
    name_str = f'''(\n    name='{default_name}',\n'''
    desc_str = f'''    description='{description}',\n''' if description else ''
    ending_str = ')\n'
    return '@dsl.pipeline' + name_str + desc_str + ending_str

def get_compile_step(func_name: str):
    return (
        f'\n'
        f'compiler.Compiler().compile(\n'
        f'    pipeline_func={func_name},\n'
        f'    package_path=pipeline_job_spec_path)\n'
        f'\n'
    )
