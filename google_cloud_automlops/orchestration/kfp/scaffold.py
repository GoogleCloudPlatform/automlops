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

"""Builds temporary component scaffold yaml files."""

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


def create_component_scaffold(func: Optional[Callable] = None,
                              *,
                              packages_to_install: Optional[List[str]] = None):
    """Creates a tmp component scaffold which will be used by the formalize function.
    Code is temporarily stored in component_spec['implementation']['container']['command'].

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install: A list of optional packages to install before
            executing func. These will always be installed at component runtime.
    """
    # Extract name, docstring, and component description
    name = func.__name__
    parsed_docstring = docstring_parser.parse(inspect.getdoc(func))
    description = parsed_docstring.short_description

    # Instantiate component yaml attributes
    component_spec = {}
    component_spec['name'] = name
    if description:
        component_spec['description'] = description
    component_spec['inputs'] = get_function_parameters(func)
    component_spec['implementation'] = {}
    component_spec['implementation']['container'] = {}
    component_spec['implementation']['container']['image'] = PLACEHOLDER_IMAGE
    component_spec['implementation']['container']['command'] = get_packages_to_install_command(func, packages_to_install)
    component_spec['implementation']['container']['args'] = ['--executor_input',
                                                             {'executorInput': None},
                                                             '--function_to_execute', 
                                                             name]
    # Write component yaml
    filename = CACHE_DIR + f'/{name}.yaml'
    make_dirs([CACHE_DIR])
    write_yaml_file(filename, component_spec, 'w')


def get_packages_to_install_command(func: Optional[Callable] = None,
                                    packages_to_install: Optional[List[str]] = None):
    """Returns a list of formatted list of commands, including code for tmp storage.

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install: A list of optional packages to install before
            executing func. These will always be installed at component runtime.
    """
    newline = '\n'
    if not packages_to_install:
        packages_to_install = []
    concat_package_list = ' '.join([repr(str(package)) for package in packages_to_install])
    install_python_packages_script = (
        f'''if ! [ -x "$(command -v pip)" ]; then{newline}'''
        f'''    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip{newline}'''
        f'''fi{newline}'''
        f'''PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \{newline}'''
        f'''    --no-warn-script-location {concat_package_list} && "$0" "$@"{newline}'''
        f'''{newline}''')
    src_code = get_function_source_definition(func)
    return ['sh', '-c', install_python_packages_script, src_code]


def get_function_parameters(func: Callable) -> dict:
    """Returns a formatted list of parameters.

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
    Returns:
        list: Params list with types converted to kubeflow spec.
    Raises:
        Exception: If parameter type hints are not provided.
    """
    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())
    parsed_docstring = docstring_parser.parse(inspect.getdoc(func))
    doc_dict = {p.arg_name: p.description for p in parsed_docstring.params}

    # Extract parameter metadata
    parameter_holder = []
    for param in parameters:
        metadata = {}
        metadata['name'] = param.name
        metadata['description'] = doc_dict.get(param.name)
        metadata['type'] = maybe_strip_optional_from_annotation(
            param.annotation)
        parameter_holder.append(metadata)
        # pylint: disable=protected-access
        if metadata['type'] == inspect._empty:
            raise TypeError(
                f'''Missing type hint for parameter "{metadata['name']}". '''
                f'''Please specify the type for this parameter.''')
    return update_params(parameter_holder)


def maybe_strip_optional_from_annotation(annotation: T) -> T:
    """Strips 'Optional' from 'Optional[<type>]' if applicable.
    For example::
        Optional[str] -> str
        str -> str
        List[int] -> List[int]
    Args:
        annotation: The original type annotation which may or may not has `Optional`.
    Returns:
        The type inside Optional[] if Optional exists, otherwise the original type.
    """
    if getattr(annotation, '__origin__', None) is Union and annotation.__args__[1] is type(None):
        return annotation.__args__[0]
    else:
        return annotation


def create_pipeline_scaffold(func: Optional[Callable] = None,
                             *,
                             name: Optional[str] = None,
                             description: Optional[str] = None):
    """Creates a temporary pipeline scaffold which will
    be used by the formalize function.

    Args:
        func: The python function to create a pipeline from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
    """
    pipeline_scaffold = (get_pipeline_decorator(name, description) +
                         get_function_source_definition(func) +
                         get_compile_step(func.__name__))
    make_dirs([CACHE_DIR]) # if it doesn't already exist
    write_file(PIPELINE_CACHE_FILE, pipeline_scaffold, 'w')


def get_pipeline_decorator(name: Optional[str] = None,
                           description: Optional[str] = None):
    """Creates the kfp pipeline decorator.

    Args:
        name: The name of the pipeline.
        description: Short description of what the pipeline does.

    Returns:
        str: Python compile function call.
    """
    default_name = DEFAULT_PIPELINE_NAME if not name else name
    name_str = f'''(\n    name='{default_name}',\n'''
    desc_str = f'''    description='{description}',\n''' if description else ''
    ending_str = ')\n'
    return '@dsl.pipeline' + name_str + desc_str + ending_str


def get_compile_step(func_name: str):
    """Creates the compile function call.

    Args:
        func_name: The name of the pipeline function.

    Returns:
        str: Python compile function call.
    """
    return (
        f'\n'
        f'compiler.Compiler().compile(\n'
        f'    pipeline_func={func_name},\n'
        f'    package_path=pipeline_job_spec_path)\n'
        f'\n'
    )
