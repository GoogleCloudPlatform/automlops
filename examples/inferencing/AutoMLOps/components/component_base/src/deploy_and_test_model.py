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
    model_directory: str,
    project_id: str,
    region: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction. Runs a prediction
       and explanation test as well.

    Args:
        model_directory: GS location of saved model.
        project_id: Project_id.
        region: Region.
    """
    from google.cloud import aiplatform
    from google.cloud.aiplatform.explain.metadata.tf.v2 import \
    saved_model_metadata_builder
    import pprint as pp

    aiplatform.init(project=project_id, location=region)

    MODEL_NAME = 'churn'
    IMAGE = "us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-5:latest"
    params = {"sampled_shapley_attribution": {"path_count": 10}}
    EXPLAIN_PARAMS = aiplatform.explain.ExplanationParameters(params)
    builder = saved_model_metadata_builder.SavedModelMetadataBuilder(
        model_path=model_directory, outputs_to_explain=["churned_probs"]
    )
    EXPLAIN_META = builder.get_metadata_protobuf()
    DEFAULT_INPUT = {
        "cnt_ad_reward": 0,
        "cnt_challenge_a_friend": 0,
        "cnt_completed_5_levels": 1,
        "cnt_level_complete_quickplay": 3,
        "cnt_level_end_quickplay": 5,
        "cnt_level_reset_quickplay": 2,
        "cnt_level_start_quickplay": 6,
        "cnt_post_score": 34,
        "cnt_spend_virtual_currency": 0,
        "cnt_use_extra_steps": 0,
        "cnt_user_engagement": 120,
        "country": "Denmark",
        "dayofweek": 3,
        "julianday": 254,
        "language": "da-dk",
        "month": 9,
        "operating_system": "IOS",
        "user_pseudo_id": "104B0770BAE16E8B53DF330C95881893",
    }

    model = aiplatform.Model.upload(
        display_name=MODEL_NAME,
        artifact_uri=model_directory,
        serving_container_image_uri=IMAGE,
        explanation_parameters=EXPLAIN_PARAMS,
        explanation_metadata=EXPLAIN_META,
        sync=True
    )

    endpoint = model.deploy(
        machine_type='n1-standard-4',
        deployed_model_display_name='deployed-churn-model')

    # Test predictions
    print('running prediction test...')
    try:
        resp = endpoint.predict([DEFAULT_INPUT])
        for i in resp.predictions:
            vals = i["churned_values"]
            probs = i["churned_probs"]
        for i in range(len(vals)):
            print(vals[i], probs[i])
        pp.pprint(resp)
    except Exception as ex:
        print("prediction request failed", ex)

    # Test explanations
    print('\nrunning explanation test...')
    try:
        features = []
        scores = []
        resp = endpoint.explain([DEFAULT_INPUT])
        for i in resp.explanations:
            for j in i.attributions:
                for k in j.feature_attributions:
                    features.append(k)
                    scores.append(j.feature_attributions[k])
        features = [x for _, x in sorted(zip(scores, features))]
        scores = sorted(scores)
        for i in range(len(scores)):
            print(scores[i], features[i])
        pp.pprint(resp)
    except Exception as ex:
        print("explanation request failed", ex)

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
