#!/bin/bash
# Submits the PipelineJob to Vertex AI
# This script should run from the AutoMLOps/ directory
# Change directory in case this is not the script root.

CONFIG_FILE=configs/defaults.yaml

python3 -m pipelines.pipeline_runner --config $CONFIG_FILE
