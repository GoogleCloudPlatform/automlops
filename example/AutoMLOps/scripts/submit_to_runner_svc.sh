#!/bin/bash
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

# Calls the Cloud Run pipeline Runner service to submit
# a PipelineJob to Vertex AI. This script should run from
# the main directory. Change directory in case this is not the script root.

PIPELINE_RUNNER_SVC_URL=`gcloud run services describe run-pipeline --platform managed --region us-central1 --format 'value(status.url)'`
curl -v --ipv4 --http1.1 --trace-ascii - $PIPELINE_RUNNER_SVC_URL \
  -X POST \
  -H "Authorization:bearer $(gcloud auth print-identity-token --quiet)" \
  -H "Content-Type: application/json" \
  --data @pipelines/runtime_parameters/pipeline_parameter_values.json
