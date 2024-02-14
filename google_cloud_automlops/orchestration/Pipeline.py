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

"""Creates a generic pipeline object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from abc import ABC, abstractmethod
from typing import Callable, Optional

from google_cloud_automlops.utils.constants import (
    DEFAULT_PIPELINE_NAME,
    GENERATED_DEFAULTS_FILE
)
from google_cloud_automlops.utils.utils import (
    get_function_source_definition,
    read_yaml_file
)


class Pipeline(ABC):
    """The Pipeline object represents a component defined by the user.

    Args:
        ABC: Abstract class
    """

    def __init__(self,
                 func: Optional[Callable] = None,
                 *,
                 name: Optional[str] = None,
                 description: Optional[str] = None):
        """Initiates a pipeline object created out of a function holding
        all necessary code.

        Args:
            func: The python function to create a pipeline from. The function
                should have type annotations for all its arguments, indicating how
                it is intended to be used (e.g. as an input/output Artifact object,
                a plain parameter, or a path to a file).
            name: The name of the pipeline.
            description: Short description of what the pipeline does.
        """
        self.func = func
        self.func_name = func.__name__
        self.name = DEFAULT_PIPELINE_NAME if not name else name
        self.description = description
        self.src_code = get_function_source_definition(self.func)

    @abstractmethod
    def build(self,
              base_image,
              custom_training_job_specs,
              pipeline_params,
              pubsub_topic_name,
              use_ci):
        """Instantiates an abstract built method to create and write pipeline files. Also
        reads in defaults file to save default arguments to attributes.

        Files created must include:
            1. README.md
            2. Dockerfile
            3. Requirements.txt

        Args:
            base_image (_type_): _description_
            custom_training_job_specs (_type_): _description_
            pipeline_params (_type_): _description_
            pubsub_topic_name (_type_): _description_
            use_ci (_type_): _description_
        """
        # Save parameters as attributes
        self.base_image = base_image
        self.custom_training_job_specs = custom_training_job_specs
        self.pipeline_params = pipeline_params
        self.pubsub_topic_name = pubsub_topic_name
        self.use_ci = use_ci

        # Extract additional attributes from defaults file
        defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
        self.project_id = defaults['gcp']['project_id']
        self.gs_pipeline_job_spec_path = defaults['pipelines']['gs_pipeline_job_spec_path']

class FuturePipeline():
    """Placeholder for future pipeline object that will be created out of a list of components.
    """
    def __init__(self, comps: list) -> None:
        self.comps = comps
        self.names = [comp.name for comp in self.comps]
