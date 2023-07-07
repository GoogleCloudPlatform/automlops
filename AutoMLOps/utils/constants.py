# Copyright 2023 Google LLC. All Rights Reserved.
#
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

"""Sets global constants."""

# pylint: disable=C0103
# pylint: disable=line-too-long

# Apache license
GENERATED_LICENSE = (
    '# Licensed under the Apache License, Version 2.0 (the "License");\n'
    '# you may not use this file except in compliance with the License.\n'
    '# You may obtain a copy of the License at\n'
    '#\n'
    '#     http://www.apache.org/licenses/LICENSE-2.0\n'
    '#\n'
    '# Unless required by applicable law or agreed to in writing, software\n'
    '# distributed under the License is distributed on an "AS IS" BASIS,\n'
    '# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n'
    '# See the License for the specific language governing permissions and\n'
    '# limitations under the License.\n'
    '#\n'
    '# DISCLAIMER: This code is generated as part of the AutoMLOps output.\n'
    '\n'
)

# Placeholder
PLACEHOLDER_IMAGE = 'AutoMLOps_image_tbd'

# AutoMLOps file paths
BASE_DIR = 'AutoMLOps/'
GENERATED_DEFAULTS_FILE = BASE_DIR + 'configs/defaults.yaml'
GENERATED_PIPELINE_SPEC_SH_FILE = BASE_DIR + 'scripts/build_pipeline_spec.sh'
GENERATED_BUILD_COMPONENTS_SH_FILE = BASE_DIR + 'scripts/build_components.sh'
GENERATED_RUN_PIPELINE_SH_FILE = BASE_DIR + 'scripts/run_pipeline.sh'
GENERATED_RUN_ALL_SH_FILE = BASE_DIR + 'scripts/run_all.sh'
GENERATED_RESOURCES_SH_FILE = BASE_DIR + 'scripts/create_resources.sh'
GENERATED_SUBMIT_JOB_FILE = BASE_DIR + 'scripts/submit_to_runner_svc.sh'
GENERATED_CLOUDBUILD_FILE = BASE_DIR + 'cloudbuild.yaml'
GENERATED_PIPELINE_FILE = BASE_DIR + 'pipelines/pipeline.py'
GENERATED_COMPONENT_BASE = BASE_DIR + 'components/component_base'
GENERATED_COMPONENT_BASE_SRC = BASE_DIR + 'components/component_base/src'
GENERATED_PARAMETER_VALUES_PATH = 'pipelines/runtime_parameters/pipeline_parameter_values.json'
GENERATED_PIPELINE_JOB_SPEC_PATH = 'scripts/pipeline_spec/pipeline_job.json'
GENERATED_DIRS = [
    BASE_DIR,
    BASE_DIR + 'components',
    BASE_DIR + 'components/component_base',
    BASE_DIR + 'components/component_base/src',
    BASE_DIR + 'configs',
    BASE_DIR + 'images',
    BASE_DIR + 'pipelines',
    BASE_DIR + 'pipelines/runtime_parameters',
    BASE_DIR + 'scripts',
    BASE_DIR + 'scripts/pipeline_spec'
]

# temporary files
CACHE_DIR = '.AutoMLOps-cache'
PIPELINE_CACHE_FILE = CACHE_DIR + '/pipeline_scaffold.py'

# KFP Spec output_file location
OUTPUT_DIR = CACHE_DIR

# Generated kfp pipeline metadata name
DEFAULT_PIPELINE_NAME = 'automlops-pipeline'

# Character substitution constants
LEFT_BRACKET = '{'
RIGHT_BRACKET = '}'
NEWLINE = '\n'

# KFP v2 Migration constant
PINNED_KFP_VERSION = 'kfp<2.0.0'
