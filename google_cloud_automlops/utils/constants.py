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
)

# Placeholder
PLACEHOLDER_IMAGE = 'AutoMLOps_image_tbd'

## Default values
# Default docker base image
DEFAULT_BASE_IMAGE = 'python:3.9-slim'
# Default location of resources
DEFAULT_RESOURCE_LOCATION = 'us-central1'
# Default naming prefix for resources
DEFAULT_NAMING_PREFIX = 'automlops-default-prefix'
# Default cloud scheduler job cron pattern
DEFAULT_SCHEDULE_PATTERN = 'No Schedule Specified'
# Default source repository branch
DEFAULT_SOURCE_REPO_BRANCH = 'automlops'
# Default vpc connector name
DEFAULT_VPC_CONNECTOR = 'No VPC Specified'

# Recommended software versions
MIN_GCLOUD_BETA_VERSION = '2022.10.21'
MIN_GCLOUD_SDK_VERSION = '420.0.0'
MIN_RECOMMENDED_TERRAFORM_VERSION = '1.5.6'

# AutoMLOps file paths
BASE_DIR = 'AutoMLOps/'
GENERATED_DEFAULTS_FILE = BASE_DIR + 'configs/defaults.yaml'
GENERATED_PIPELINE_SPEC_SH_FILE = BASE_DIR + 'scripts/build_pipeline_spec.sh'
GENERATED_BUILD_COMPONENTS_SH_FILE = BASE_DIR + 'scripts/build_components.sh'
GENERATED_RUN_PIPELINE_SH_FILE = BASE_DIR + 'scripts/run_pipeline.sh'
GENERATED_RUN_ALL_SH_FILE = BASE_DIR + 'scripts/run_all.sh'
GENERATED_RESOURCES_SH_FILE = BASE_DIR + 'provision/provision_resources.sh'
GENERATED_PUBLISH_TO_TOPIC_FILE = BASE_DIR + 'scripts/publish_to_topic.sh'
GENERATED_CLOUDBUILD_FILE = BASE_DIR + 'cloudbuild.yaml'
GENERATED_PIPELINE_REQUIREMENTS_FILE = BASE_DIR + 'pipelines/requirements.txt'
GENERATED_PIPELINE_FILE = BASE_DIR + 'pipelines/pipeline.py'
GENERATED_PIPELINE_RUNNER_FILE = BASE_DIR + 'pipelines/pipeline_runner.py'
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
    BASE_DIR + 'scripts/pipeline_spec',
]

GENERATED_SERVICES_DIRS = [
    BASE_DIR + 'services',
    BASE_DIR + 'services/submission_service'
]

GENERATED_PROVISION_DIRS = [
    BASE_DIR + 'provision'
]

GENERATED_TERRAFORM_DIRS = [
    BASE_DIR + 'provision/state_bucket',
    BASE_DIR + 'provision/environment',
]

# temporary files
CACHE_DIR = '.AutoMLOps-cache'
PIPELINE_CACHE_FILE = CACHE_DIR + '/pipeline_scaffold.py'

# KFP Spec output_file location
OUTPUT_DIR = CACHE_DIR

# Generated kfp pipeline metadata name
DEFAULT_PIPELINE_NAME = 'automlops-pipeline'

# KFP v2 Migration constant
PINNED_KFP_VERSION = 'kfp<2.0.0'

# Provisioning Template Paths
TERRAFORM_TEMPLATES_PATH = 'google_cloud_automlops.provisioning.terraform.templates'
PULUMI_TEMPLATES_PATH = 'google_cloud_automlops.provisioning.pulumi.templates'
GCLOUD_TEMPLATES_PATH = 'google_cloud_automlops.provisioning.gcloud.templates'
KFP_TEMPLATES_PATH = 'google_cloud_automlops.orchestration.kfp.templates'
CLOUDBUILD_TEMPLATES_PATH = 'google_cloud_automlops.deployments.cloudbuild.templates'
GITOPS_TEMPLATES_PATH = 'google_cloud_automlops.deployments.gitops.templates'

# Required IAM Roles for pipeline runner service account
IAM_ROLES_RUNNER_SA = set([
    'roles/aiplatform.user',
    'roles/artifactregistry.reader',
    'roles/bigquery.user',
    'roles/bigquery.dataEditor',
    'roles/iam.serviceAccountUser',
    'roles/storage.admin',
    'roles/cloudfunctions.admin'
])
