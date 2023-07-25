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

def test_monitoring_job(
    data_source: str,
    project_id: str,
    region: str,
    target: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction. Runs a prediction
       and explanation test as well.

    Args:
        data_source: BQ training data table.
        project_id: Project_id.
        region: Region.
        target: Prediction target column name in training dataset.
    """
    import time

    from google.cloud import aiplatform
    from google.cloud import bigquery

    bq_client = bigquery.Client(project=project_id)
    # Download the table.
    table = bigquery.TableReference.from_string(data_source[5:])

    rows = bq_client.list_rows(table, max_results=1000)

    instances = []
    for row in rows:
        instance = {}
        for key, value in row.items():
            if key == target:
                continue
            if value is None:
                value = ""
            instance[key] = value
        instances.append(instance)

    print(len(instances))

    endpoint = aiplatform.Endpoint.list(filter='display_name="churn_endpoint"')[0]
    response = endpoint.predict(instances=instances)
    prediction = response[0]
    # print the predictions
    print(prediction)

    # Pause a bit for the baseline distribution to be calculated
    time.sleep(120)

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
