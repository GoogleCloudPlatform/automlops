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
from kfp.v2.components import executor

import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import *
from typing import *

def deploy_and_test_model(
    endpoint_sa: str,
    project_id: str,
    region: str,
    serving_image_tag: str
):
    """Custom component that uploads a finetuned Flan-T5 from GCS to Vertex Model Registry,
       deploys the model to an endpoint for online prediction, and runs a prediction test.

    Args:
        endpoint_sa: Service account to run the endpoint prediction service with.
        project_id: Project_id.
        region: Region.
        serving_image_tag: Custom serving image uri.
    """
    import pprint as pp
    from random import randrange

    from google.cloud import aiplatform

    from datasets import load_dataset

    DATASET_ID = 'samsum'

    aiplatform.init(project=project_id, location=region)
    # Check if model exists
    models = aiplatform.Model.list()
    model_name = 'finetuned-flan-t5'
    if 'finetuned-flan-t5' in (m.name for m in models):
        parent_model = model_name
        model_id = None
        is_default_version=False
        version_aliases=['experimental', 'finetuned', 'flan-t5']
        version_description='experimental version'
    else:
        parent_model = None
        model_id = model_name
        is_default_version=True
        version_aliases=['live', 'finetuned', 'flan-t5']
        version_description='live version'

    uploaded_model = aiplatform.Model.upload(
        model_id=model_id,
        display_name=model_name,
        parent_model=parent_model,
        is_default_version=is_default_version,
        version_aliases=version_aliases,
        version_description=version_description,
        serving_container_image_uri=serving_image_tag,
        serving_container_predict_route='/predict',
        serving_container_health_route='/health',
        serving_container_ports=[8080],
        labels={'created_by': 'automlops-team'},
    )

    endpoint = uploaded_model.deploy(
        machine_type='n1-standard-8',
        min_replica_count=1,
        max_replica_count=1,
        accelerator_type='NVIDIA_TESLA_V100',    
        accelerator_count=1,
        service_account=endpoint_sa, # This SA needs gcs permissions
        sync=True
    )

    # Load dataset from the hub
    dataset = load_dataset(DATASET_ID)
    # select a random test sample
    sample = dataset['test'][randrange(len(dataset["test"]))]

    # Test predictions
    print('running prediction test...')
    try:
        resp = endpoint.predict([[sample['dialogue']]])
        print(sample['dialogue'])
        pp.pprint(resp)
    except Exception as ex:
        print('prediction request failed', ex)

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
