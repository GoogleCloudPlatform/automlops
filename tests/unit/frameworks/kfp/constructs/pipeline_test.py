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

from mock import patch
import mock
import pytest
import os
import AutoMLOps.utils.constants
from AutoMLOps.frameworks.kfp.constructs.pipeline import KfpPipeline
from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    NEWLINE,
    LEFT_BRACKET,
    RIGHT_BRACKET,
    GENERATED_COMPONENT_BASE,
    CACHE_DIR,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_JOB_SPEC_PATH,
)


@pytest.mark.parametrize(
    """custom_training_job_specs, defaults_file""",
    [
        (
            [
                {
                    "component_spec": "train_model",
                    "display_name": "train-model-accelerated",
                    "machine_type": "a2-highgpu-1g",
                    "accelerator_type": "NVIDIA_TESLA_A100",
                    "accelerator_count": "1",
                }
            ],
            "tests/unit/test_data/defaults.yaml",
        )
    ],
)
def test_init(mocker, custom_training_job_specs, defaults_file):
    """Tests the initialization of the KFPPipeline class."""

    #patch global directory variables
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')

    # Create pipeline object
    pipeline = KfpPipeline(
        custom_training_job_specs=custom_training_job_specs,
        defaults_file=defaults_file
    )

    #define variables needed for assertions
    gcpc_imports = (
        'from functools import partial\n'
        'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component\n')
    quote = '\''
    newline_tab = '\n    '
    components_list = ''
    custom_specs = pipeline.custom_specs_helper(custom_training_job_specs)

    # Assert object properties were created properly
    assert pipeline.pipeline_imports == (
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
            f'''{custom_specs}''')
    
    assert pipeline.pipeline_argparse == (
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

    # # Remove temporary files
    # os.remove("test_temp_dir/requirements.txt")
    # os.rmdir("test_temp_dir")
