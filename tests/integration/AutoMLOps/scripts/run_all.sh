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

# Builds components, pipeline specs, and submits the PipelineJob.
# This script should run from the AutoMLOps/ directory
# Change directory in case this is not the script root.

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN} BUILDING COMPONENTS ${NC}"
gcloud builds submit .. --config cloudbuild.yaml --timeout=3600

echo -e "${GREEN} BUILDING PIPELINE SPEC ${NC}"
./scripts/build_pipeline_spec.sh

echo -e "${GREEN} RUNNING PIPELINE JOB ${NC}"
./scripts/run_pipeline.sh