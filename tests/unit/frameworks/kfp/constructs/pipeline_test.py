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

"""Unit tests for component constructs kfp module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

import pytest
from AutoMLOps.frameworks.kfp.constructs.pipeline import KfpPipeline
from AutoMLOps.utils.constants import GENERATED_LICENSE
from AutoMLOps.utils.utils import format_spec_dict, get_components_list
from AutoMLOps.utils.utils import write_yaml_file
import AutoMLOps.utils.utils

# Create defaults file contents to test
DEFAULTS1 = {
    'gcp':
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }
DEFAULTS2 = {
    'gcp':
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }

@pytest.fixture(params=[DEFAULTS1, DEFAULTS2])
def defaults_dict(request, tmpdir):
    """Writes temporary yaml file fixture using defaults parameterized dictionaries 
    during pytest session scope.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """
    yaml_path = tmpdir.join('test.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}

@pytest.mark.parametrize(
    'custom_training_job_specs',
    [
        [{'component_spec': 'mycomp1', 'other': 'myother'}],
        [
            {
                "component_spec": "train_model",
                "display_name": "train-model-accelerated",
                "machine_type": "a2-highgpu-1g",
                "accelerator_type": "NVIDIA_TESLA_A100",
                "accelerator_count": "1",
            }
        ]
    ]
)
def test_KfpPipeline(mocker, custom_training_job_specs, defaults_dict):
    """Tests the KFP child class that generates files related to KFP pipelines.

    Args:
        custom_training_job_specs (List[Dict]): Specifies the specs to run the training job with.
        defaults_file (dict): Dictionary containing the path to the default config
            variables yaml and the dictionary held within it.
    """
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')

    # Extract path and contents from defaults dict to create KFP Component
    path = defaults_dict['path']
    defaults = defaults_dict['vals']
    gcpc_imports = (
        'from functools import partial\n'
        'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component\n')
    quote = '\''
    newline_tab = '\n    '

    pipe = KfpPipeline(custom_training_job_specs=custom_training_job_specs, defaults_file=path)
    custom_specs = pipe.custom_specs_helper(custom_training_job_specs)

    assert pipe._project_id == defaults['gcp']['project_id']
    assert pipe._custom_training_job_specs == custom_training_job_specs

    assert pipe.pipeline_imports == (
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
        f'''    {newline_tab.join(f'{component} = load_custom_component(component_name={quote}{component}{quote})' for component in get_components_list(full_path=False))}\n'''
        f'\n'
        f'''{custom_specs}''')

    assert pipe.pipeline_argparse == (
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

    assert pipe.pipeline_runner == (
        GENERATED_LICENSE +
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