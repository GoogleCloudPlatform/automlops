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

from typing import Callable, Optional

from google_cloud_automlops.utils.constants import DEFAULT_PIPELINE_NAME
from google_cloud_automlops.utils.utils import get_function_source_definition


class Pipeline():
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

class FuturePipeline():
    def __init__(self, comps: list) -> None:
        self.comps = comps
        self.names = [comp.name for comp in self.comps]
