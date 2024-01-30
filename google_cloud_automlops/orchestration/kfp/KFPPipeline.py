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

"""Creates a KFP pipeline object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Callable, Optional
from google_cloud_automlops.orchestration.Pipeline import Pipeline

from google_cloud_automlops.utils.constants import (
    CACHE_DIR,
    PIPELINE_CACHE_FILE
)
from google_cloud_automlops.utils.utils import (
    make_dirs,
    write_file
)


class KFPPipeline(Pipeline):
    def __init__(self, 
                 func: Optional[Callable] = None,
                 *,
                 name: Optional[str] = None,
                 description: Optional[str] = None) -> None:
        """Initiates a KFP pipeline object created out of a function holding
        all necessary code.

        Args:
            func: The python function to create a pipeline from. The function
                should have type annotations for all its arguments, indicating how
                it is intended to be used (e.g. as an input/output Artifact object,
                a plain parameter, or a path to a file).
            name: The name of the pipeline.
            description: Short description of what the pipeline does.
        """
        super().__init__(func, name, description)
        self.pipeline_scaffold = (self._get_pipeline_decorator() + 
                                  self.src_code +
                                  self._get_compile_step())

    def build(self):
        """Constructs files for running and managing Kubeflow pipelines.
        """
        make_dirs([CACHE_DIR]) # if it doesn't already exist
        write_file(PIPELINE_CACHE_FILE, self.pipeline_scaffold, 'w')

    def _get_pipeline_decorator(self):
        """Creates the kfp pipeline decorator.

        Args:
            name: The name of the pipeline.
            description: Short description of what the pipeline does.

        Returns:
            str: Python compile function call.
        """
        name_str = f'''(\n    name='{self.name}',\n'''
        desc_str = f'''    description='{self.description}',\n''' if self.description else ''
        ending_str = ')\n'
        return '@dsl.pipeline' + name_str + desc_str + ending_str

    def _get_compile_step(self):
        """Creates the compile function call.

        Args:
            func_name: The name of the pipeline function.

        Returns:
            str: Python compile function call.
        """
        return (
            f'\n'
            f'compiler.Compiler().compile(\n'
            f'    pipeline_func={self.func_name},\n'
            f'    package_path=pipeline_job_spec_path)\n'
            f'\n'
        )
