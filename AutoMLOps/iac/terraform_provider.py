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

"""Builds Terraform Files"""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import

from AutoMLOps.utils.utils import (
    write_file,
    make_dirs,
)

from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    RIGHT_BRACKET,
    LEFT_BRACKET,
    NEWLINE,
)

from AutoMLOps.iac.configs import TerraformConfig


def builder(
    project_id: str,
    config: TerraformConfig,
):
    """Constructs and writes pulumi scripts: Generates infrastructure using pulumi resource management style.

    Args:
    .......
    ......
    .....
    """

    # Define the model name for the IaC configurations
    # remove special characters and spaces
    pipeline_model_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.pipeline_model_name]).lower()

    print(f"pipeline_model_name: {pipeline_model_name}")
