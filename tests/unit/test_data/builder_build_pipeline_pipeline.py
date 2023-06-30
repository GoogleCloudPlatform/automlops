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

import argparse
import os
from functools import partial
from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component
import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import *
from typing import *
import yaml

def load_custom_component(component_name: str):
    component_path = os.path.join('components',
                                component_name,
                              'component.yaml')
    return kfp.components.load_component_from_file(component_path)

def create_training_pipeline(pipeline_job_spec_path: str):
    

    train_model_custom_training_job_specs = {
       'component_spec': train_model,
       'display_name': 'train-model-accelerated',
       'machine_type': 'a2-highgpu-1g',
       'accelerator_type': 'NVIDIA_TESLA_A100',
       'accelerator_count': '1',
    }

    train_model_job_op = create_custom_training_job_op_from_component(**train_model_custom_training_job_specs)
    train_model = partial(train_model_job_op, project='my_project')
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                       help='The config file for setting default values.')

    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    pipeline = create_training_pipeline(
        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])
