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
    batch_predict = load_custom_component(component_name='batch_predict')

    @dsl.pipeline(
        name='automlops-pipeline',
    )
    def pipeline(bq_table: str,
                 data_path: str,
                 project_id: str,
                 bigquery_destination: str,
                 bq_dataset_path: str,
                 instances_format: str,
                 predictions_format: str,
                 model_resource_name: str,
                 endpoint_resource_name: str,
                 machine_type: str,
                 accelerator_count: int,
                 accelerator_type: str,
                 max_replica_count: int,
                 starting_replica_count: int
                ):
    
        batch_predict_task = batch_predict(
                 project_id=project_id,
                 bigquery_destination=bigquery_destination,
                 bq_dataset_path=bq_dataset_path,
                 instances_format=instances_format,
                 predictions_format=predictions_format,
                 model_resource_name=model_resource_name,
                 endpoint_resource_name=endpoint_resource_name,
                 machine_type=machine_type,
                 accelerator_count=accelerator_count,
                 accelerator_type=accelerator_type,
                 max_replica_count=max_replica_count,
                 starting_replica_count=starting_replica_count)
    
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_job_spec_path)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                       help='The config file for setting default values.')

    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    pipeline = create_training_pipeline(
        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])
