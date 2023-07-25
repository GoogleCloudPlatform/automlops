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
    test_monitoring_job = load_custom_component(component_name='test_monitoring_job')
    deploy_and_test_model = load_custom_component(component_name='deploy_and_test_model')
    create_monitoring_job = load_custom_component(component_name='create_monitoring_job')

    @dsl.pipeline(
        name='automlops-monitoring-pipeline',
        description='This is an example model monitoring pipeline',
    )
    def pipeline(alert_emails: list,
                 cnt_user_engagement_threshold_value: float,
                 country_threshold_value: float,
                 data_source: str,
                 log_sampling_rate: float,
                 model_directory: str,
                 monitor_interval: int,
                 project_id: str,
                 region: str,
                 target: str):
    
        deploy_and_test_model_task = deploy_and_test_model(
            model_directory=model_directory,
            project_id=project_id,
            region=region)
    
        create_monitoring_job_task = create_monitoring_job(
            alert_emails=alert_emails,
            cnt_user_engagement_threshold_value=cnt_user_engagement_threshold_value,
            country_threshold_value=country_threshold_value,
            data_source=data_source,
            log_sampling_rate=log_sampling_rate,
            monitor_interval=monitor_interval,
            project_id=project_id,
            region=region,
            target=target).after(deploy_and_test_model_task)
    
        test_monitoring_job_task = test_monitoring_job(
            data_source=data_source,
            project_id=project_id,
            region=region,
            target=target).after(create_monitoring_job_task)
    
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
