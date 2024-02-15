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

"""Model classes for AutoMLOps Orchestration Frameworks."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Dict, List, Optional

from pydantic import BaseModel


class KfpConfig(BaseModel):
    """Model representing the KFP config.

    Args:
        base_image: The image to use in the component base dockerfile.
        custom_training_job_specs: Specifies the specs to run the training job with.
        pipeline_params: Dictionary containing runtime pipeline parameters.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        use_ci: Flag that determines whether to use Cloud Run CI/CD.
    """
    base_image: str
    custom_training_job_specs: Optional[List]
    pipeline_params: Dict
    pubsub_topic_name: str
    use_ci: bool
