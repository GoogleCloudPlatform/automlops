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

"""XXX"""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

import inspect
from typing import Callable, List, Optional, TypeVar, Union

import docstring_parser

from google_cloud_automlops.utils.constants import (
    DEFAULT_PIPELINE_NAME,
    PLACEHOLDER_IMAGE,
    PIPELINE_CACHE_FILE,
    CACHE_DIR
)
from google_cloud_automlops.utils.utils import (
    get_function_source_definition,
    make_dirs,
    update_params,
    write_file,
    write_yaml_file
)

T = TypeVar('T')

def create_task_scaffold(func: Optional[Callable] = None,
                         *,
                         packages_to_install: Optional[List[str]] = None):
    """Creates a tmp task scaffold which will be used by the formalize function.
    Code is temporarily stored in component_spec['implementation']['container']['command'].

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install: A list of optional packages to install before
            executing func. These will always be installed at component runtime.
    """
    # Extract name, docstring, and task description
    name = func.__name__
    parsed_docstring = docstring_parser.parse(inspect.getdoc(func))
    description = parsed_docstring.short_description
    
    # Instantiate component attributes
    component_spec = {}
    component_spec['python_callable'] = name
    component_spec['task_id'] = name + "_task"
    component_spec['requirements'] = packages_to_install if packages_to_install else []