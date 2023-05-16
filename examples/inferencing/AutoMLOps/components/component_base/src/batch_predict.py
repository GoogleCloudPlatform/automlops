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
import json
import kfp
from kfp.v2 import dsl
from kfp.v2.components import executor
from kfp.v2.dsl import *
from typing import *

def batch_predict(
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
    """Runs a batch prediction job.

    Args:
        bigquery_destination: The BQ uri to store the prediction results.
        bq_dataset_path: The BQ uri of the input data to run predictions on.
        instances_format: The format in which instances are given, must be one of 'jsonl', 'csv', 'bigquery', 'tf-record', 'tf-record-gzip', or 'file-list'.
        predictions_format: The format to output the predictions, must be one of 'jsonl', 'csv', or 'bigquery'.
        model_resource_name: The fully-qualified resource name or ID for model e.g. projects/297370817971/locations/{region}/models/4540613586807947264
        endpoint_resource_name: The fully-qualified resource name or ID for endpoint e.g. projects/297370817971/locations/{region}/endpoints/1242430547200835584
        machine_type: The machine type to serve the prediction requests.
        accelerator_count: The number of accelerators to attach to the `machine_type`.
        accelerator_type: The type of accelerators that may be attached to the machine as per `accelerator_count`.
        max_replica_count: The maximum number of machine replicas the batch operation may be scaled to.
        starting_replica_count: The number of machine replicas used at the start of the batch operation.
    """
    import logging

    from google.cloud import aiplatform
    from google.cloud.aiplatform.compat.types import job_state_v1

    def _get_endpoint(resource_name: str) -> aiplatform.Endpoint:
        return aiplatform.Endpoint(resource_name)

    def _get_model(resource_name: str) -> aiplatform.Model:
        return aiplatform.Model(resource_name)

    def _get_model_from_endpoint(endpoint: aiplatform.Endpoint) -> aiplatform.Model:
        current_deployed_model_id = None

        traffic_split = endpoint.gca_resource.traffic_split
        for key in traffic_split:
            if traffic_split[key] == 100:
                current_deployed_model_id = key
            break

        if current_deployed_model_id:
            for deployed_model in endpoint.gca_resource.deployed_models:
                if deployed_model.id == current_deployed_model_id:
                    return aiplatform.Model(deployed_model.model)


    logging.info(f'input dataset URI: {bq_dataset_path}')

    # Call Vertex AI custom job in another region
    aiplatform.init(project=project_id)

    if model_resource_name:
        model = _get_model(model_resource_name)
    elif endpoint_resource_name:
        model = _get_model_from_endpoint(_get_endpoint(endpoint_resource_name))
    else:
        raise ValueError('model or endpoint resource name must be provided!')

    logging.info(f'retrieved model URI: {model.uri}')

    batch_pred_job = model.batch_predict(
        job_display_name='batch-prediction',
        bigquery_source=bq_dataset_path,
        bigquery_destination_prefix=bigquery_destination,
        instances_format=instances_format,
        predictions_format=predictions_format,
        machine_type=machine_type,
        accelerator_count=accelerator_count,
        accelerator_type=accelerator_type,
        starting_replica_count=starting_replica_count,
        max_replica_count=max_replica_count,
        sync=True)

    logging.info(f'batch prediction job: {batch_pred_job.resource_name}')

    batch_pred_job.wait()
    if batch_pred_job.state == job_state_v1.JobState.JOB_STATE_SUCCEEDED:
        logging.info(f'batch prediction job has finished with info: '
                     f'{batch_pred_job.completion_stats}')
        logging.info(f'Predictions can be found at: '
                     f'{batch_pred_job.output_info.gcs_output_directory}')
    else:
        raise RuntimeError(batch_pred_job.error)

def main():
    """Main executor."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--executor_input', type=str)
    parser.add_argument('--function_to_execute', type=str)

    args, _ = parser.parse_known_args()
    executor_input = json.loads(args.executor_input)
    function_to_execute = globals()[args.function_to_execute]

    executor.Executor(
        executor_input=executor_input,
        function_to_execute=function_to_execute).execute()

if __name__ == '__main__':
    main()
