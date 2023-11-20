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

"""Builds KFP components and pipeline."""

# pylint: disable=line-too-long

import json
try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files
import re
import textwrap

from jinja2 import Template

from google_cloud_automlops.utils.utils import (
    execute_process,
    get_components_list,
    make_dirs,
    read_file,
    read_yaml_file,
    is_using_kfp_spec,
    write_and_chmod,
    write_file,
    write_yaml_file
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_BUILD_COMPONENTS_SH_FILE,
    GENERATED_DEFAULTS_FILE,
    GENERATED_COMPONENT_BASE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_FILE,
    GENERATED_PIPELINE_REQUIREMENTS_FILE,
    GENERATED_PIPELINE_RUNNER_FILE,
    GENERATED_PIPELINE_SPEC_SH_FILE,
    GENERATED_PUBLISH_TO_TOPIC_FILE,
    GENERATED_RUN_PIPELINE_SH_FILE,
    GENERATED_RUN_ALL_SH_FILE,
    KFP_TEMPLATES_PATH,
    PINNED_KFP_VERSION,
    PIPELINE_CACHE_FILE
)
from google_cloud_automlops.orchestration.configs import AirflowConfig

def build(config: AirflowConfig):
    """Constructs files for running and managing Airflow DAGs.

    Args:
        config.base_image: The image to use in the component base dockerfile.
    """

    # IN PROGRESS