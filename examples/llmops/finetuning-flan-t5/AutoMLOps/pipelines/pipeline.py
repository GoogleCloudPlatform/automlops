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
    deploy_and_test_model = load_custom_component(component_name='deploy_and_test_model')
    finetune_t5_model = load_custom_component(component_name='finetune_t5_model')

    finetune_t5_model_custom_training_job_specs = {
       'component_spec': finetune_t5_model,
       'display_name': 'flan-t5-base-finetuning-gpu-tensorboard',
       'machine_type': 'n1-standard-32',
       'accelerator_type': 'NVIDIA_TESLA_V100',
       'accelerator_count': '4',
       'replica_count': '1',
       'service_account': 'vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com',
       'tensorboard': 'projects/45373616427/locations/us-central1/tensorboards/7295189281549582336',
       'base_output_directory': 'gs://automlops-sandbox-bucket/finetune_t5_model/',
    }

    finetune_t5_model_job_op = create_custom_training_job_op_from_component(**finetune_t5_model_custom_training_job_specs)
    finetune_t5_model = partial(finetune_t5_model_job_op, project='automlops-sandbox')
    @dsl.pipeline(
        name='finetune-flan-t5-pipeline',
    )
    def pipeline(
        endpoint_sa: str,
        project_id: str,
        eval_batch: int,
        train_batch: int,
        model_dir: str,
        lr: float,
        epochs: int,
        logging_steps: int,
        serving_image_tag: str,
        region: str):
    
        finetune_t5_model_task = finetune_t5_model(
            model_dir=model_dir,
            epochs=epochs,
            eval_batch=eval_batch,
            lr=lr,
            logging_steps=logging_steps,
            train_batch=train_batch)
    
        deploy_and_test_model_task = deploy_and_test_model(
            endpoint_sa=endpoint_sa,
            project_id=project_id,
            region=region,
            serving_image_tag=serving_image_tag).after(finetune_t5_model_task)
    
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
