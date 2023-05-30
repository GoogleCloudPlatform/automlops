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
    custom_train_model = load_custom_component(component_name='custom_train_model')

    custom_train_model_custom_training_job_specs = {
       'component_spec': custom_train_model,
       'display_name': 'train-model-accelerated',
       'machine_type': 'a2-highgpu-1g',
       'accelerator_type': 'NVIDIA_TESLA_A100',
       'accelerator_count': '1',
    }

    custom_train_model_job_op = create_custom_training_job_op_from_component(**custom_train_model_custom_training_job_specs)
    custom_train_model = partial(custom_train_model_job_op, project='automlops-sandbox')
    @dsl.pipeline(
        name='tensorflow-gpu-example',
    )
    def pipeline(
        project_id: str,
        model_dir: str,
        lr: float,
        epochs: int,
        steps: int,
        serving_image: str,
        distribute: str,
    ):
        from google_cloud_pipeline_components.types import artifact_types
        from google_cloud_pipeline_components.v1.model import ModelUploadOp
        from kfp.v2.components import importer_node
    
        custom_train_model_task = custom_train_model(
            model_dir=model_dir,
            lr=lr,
            epochs=epochs,
            steps=steps,
            distribute=distribute
        )
    
        unmanaged_model_importer = importer_node.importer(
            artifact_uri=model_dir,
            artifact_class=artifact_types.UnmanagedContainerModel,
            metadata={
                'containerSpec': {
                    'imageUri': serving_image
                }
            },
        )
    
        model_upload_op = ModelUploadOp(
            project=project_id,
            display_name='tensorflow_gpu_example',
            unmanaged_container_model=unmanaged_model_importer.outputs['artifact'],
        )
        model_upload_op.after(custom_train_model_task)
    
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
