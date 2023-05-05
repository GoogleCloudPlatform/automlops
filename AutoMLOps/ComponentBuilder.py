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

"""Builds component files."""

# pylint: disable=C0103
# pylint: disable=line-too-long

import inspect
from typing import Callable, List, Optional, TypeVar, Union

import docstring_parser
from AutoMLOps import BuilderUtils
from AutoMLOps import ScriptsBuilder

T = TypeVar('T')

def formalize(component_path: str,
              top_lvl_name: str,
              defaults_file: str,
              use_kfp_spec: bool):
    """Constructs and writes component.yaml and {component_name}.py files.
        component.yaml: Contains the Kubeflow custom component definition.
        {component_name}.py: Contains the python code from the Jupyter cell.

    Args:
        component_path: Path to the temporary component yaml. This file
            is used to create the permanent component.yaml, and deleted
            after calling AutoMLOps.generate().
        top_lvl_name: Top directory name.
        defaults_file: Path to the default config variables yaml.
        use_kfp_spec: Flag that determines the format of the component yamls.
    """
    # Read in component specs
    component_spec = BuilderUtils.read_yaml_file(component_path)

    # If using kfp, remove spaces in name and convert to lowercase
    if use_kfp_spec:
        component_spec['name'] = component_spec['name'].replace(' ', '_').lower()

    # Set and create directory for component, and set directory for task
    component_dir = top_lvl_name + 'components/' + component_spec['name']
    task_filepath = (top_lvl_name 
                     + 'components/component_base/src/' 
                     + component_spec['name'] 
                     + '.py')
    BuilderUtils.make_dirs([component_dir])

    # Initialize component scripts builder
    component_scripts = ScriptsBuilder.Component(component_spec, defaults_file)

    # Write task script to component base
    BuilderUtils.write_file(task_filepath, component_scripts.task, 'w+')

    # Update component_spec to include correct image and startup command
    component_spec['implementation']['container']['image'] = component_scripts.compspec_image
    component_spec['implementation']['container']['command'] = [
        'python3',
        f'''/pipelines/component/src/{component_spec['name']+'.py'}''']

    # Write license and component spec to the appropriate component.yaml file
    filename = component_dir + '/component.yaml'
    BuilderUtils.write_file(filename, BuilderUtils.LICENSE, 'w')
    BuilderUtils.write_yaml_file(filename, component_spec, 'a')

def create_component_scaffold(func: Optional[Callable] = None,
                              *,
                              packages_to_install: Optional[List[str]] = None):
    """Creates a tmp component scaffold which will be used by
       the formalize function. Code is temporarily stored in
       component_spec['implementation']['container']['command'].

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
    component_spec['inputs'] = _get_function_parameters(func)
    component_spec['implementation'] = {}
    component_spec['implementation']['container'] = {}
    component_spec['implementation']['container']['image'] = 'TBD'
    component_spec['implementation']['container']['command'] = _get_packages_to_install_command(func, packages_to_install)
    component_spec['implementation']['container']['args'] = ['--executor_input',
                                                             {'executorInput': None},
                                                             '--function_to_execute', 
                                                             name]

    # Write component yaml
    filename = BuilderUtils.TMPFILES_DIR + f'/{name}.yaml'
    BuilderUtils.make_dirs([BuilderUtils.TMPFILES_DIR]) 
    BuilderUtils.write_yaml_file(filename, component_spec, 'w')

def _get_packages_to_install_command(func: Optional[Callable] = None,
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
    src_code = BuilderUtils.get_function_source_definition(func)
    return ['sh', '-c', install_python_packages_script, src_code]

def _get_function_parameters(func: Callable) -> dict:
    """Needed"""
    # Extract component details from signature and docstring
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
        metadata['type'] = _maybe_strip_optional_from_annotation(param.annotation)
        parameter_holder.append(metadata)
        if metadata['type'] == inspect._empty:
            raise TypeError(
                f'''Missing type hint for parameter "{metadata['name']}". '''
                f'''Please specify the type for this parameter.''')
    return BuilderUtils.update_params(parameter_holder)

def _maybe_strip_optional_from_annotation(annotation: T) -> T:
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