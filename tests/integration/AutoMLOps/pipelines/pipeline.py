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

"""Kubeflow Pipeline Definition"""

import argparse
from typing import *
import os

from google.cloud import storage
import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import *
import yaml

def upload_pipeline_spec(gs_pipeline_job_spec_path: str,
                         pipeline_job_spec_path: str,
                         storage_bucket_name: str):
    '''Upload pipeline job spec from local to GCS'''
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(storage_bucket_name)
    filename = '/'.join(gs_pipeline_job_spec_path.split('/')[3:])
    blob = bucket.blob(filename)
    blob.upload_from_filename(pipeline_job_spec_path)

def load_custom_component(component_name: str):
    component_path = os.path.join('components',
                                component_name,
                              'component.yaml')
    return kfp.components.load_component_from_file(component_path)

def create_training_pipeline(pipeline_job_spec_path: str):
    create_dataset = load_custom_component(component_name='create_dataset')
    train_model = load_custom_component(component_name='train_model')
    deploy_model = load_custom_component(component_name='deploy_model')

    @dsl.pipeline(
        name='automlops-pipeline',
    )
    def pipeline(bq_table: str,
                model_directory: str,
                data_path: str,
                project_id: str,
                region: str,
                ):

        create_dataset_task = create_dataset(
            bq_table=bq_table,
            data_path=data_path,
            project_id=project_id)

        train_model_task = train_model(
            model_directory=model_directory,
            data_path=data_path).after(create_dataset_task)

        deploy_model_task = deploy_model(
            model_directory=model_directory,
            project_id=project_id,
            region=region).after(train_model_task)

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

    create_training_pipeline(
        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])

    upload_pipeline_spec(
        gs_pipeline_job_spec_path=config['pipelines']['gs_pipeline_job_spec_path'],
        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'],
        storage_bucket_name=config['gcp']['storage_bucket_name'])
