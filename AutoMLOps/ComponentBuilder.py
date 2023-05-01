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
    component_spec = BuilderUtils.read_yaml_file(component_path)
    if use_kfp_spec:
        component_spec['name'] = component_spec['name'].replace(' ', '_').lower()
    component_dir = top_lvl_name + 'components/' + component_spec['name']
    task_filepath = (top_lvl_name + 'components/component_base/src/' +
                     component_spec['name'] + '.py')
    BuilderUtils.make_dirs([component_dir])
    create_task(component_spec, task_filepath, use_kfp_spec)
    create_component(component_spec, component_dir, defaults_file)

def create_task(component_spec: dict, task_filepath: str, use_kfp_spec: bool):
    """Writes cell python code to a file with required imports.

    Args:
        component_spec: Component definition dictionary.
            Contains cell code which is temporarily stored in
            component_spec['implementation']['container']['command']
        task_filepath: Path to the file to be written.
        use_kfp_spec: Flag that determines the format of the component yamls.
    Raises:
        Exception: If the imports tmpfile does not exist.
    """
    custom_code = component_spec['implementation']['container']['command'][-1]
    default_imports = (BuilderUtils.LICENSE +
        'import argparse\n'
        'import json\n'
        'from kfp.v2.components import executor\n')
    if not use_kfp_spec:
        custom_imports = ('import kfp\n'
        'from kfp.v2 import dsl\n'
        'from kfp.v2.dsl import *\n'
        'from typing import *\n'
        '\n')
    else:
        custom_imports = '' # included as part of the kfp spec
    main_func = (
        '\n'
        '''def main():\n'''
        '''    """Main executor."""\n'''
        '''    parser = argparse.ArgumentParser()\n'''
        '''    parser.add_argument('--executor_input', type=str)\n'''
        '''    parser.add_argument('--function_to_execute', type=str)\n'''
        '\n'
        '''    args, _ = parser.parse_known_args()\n'''
        '''    executor_input = json.loads(args.executor_input)\n'''
        '''    function_to_execute = globals()[args.function_to_execute]\n'''
        '\n'
        '''    executor.Executor(\n'''
        '''        executor_input=executor_input,\n'''
        '''        function_to_execute=function_to_execute).execute()\n'''
        '\n'
        '''if __name__ == '__main__':\n'''
        '''    main()\n''')
    f_contents = default_imports + custom_imports + custom_code + main_func
    BuilderUtils.write_file(task_filepath, f_contents, 'w+')

def create_component(component_spec: dict,
                     component_dir: str,
                     defaults_file: str):
    """Updates the component_spec to include the correct image
       and startup command, then writes the component.yaml.
       Requires a defaults.yaml config to pull config vars from.

    Args:
        component_spec: Component definition dictionary.
        component_dir: Path of the component directory.
        defaults_file: Path to the default config variables yaml.
    Raises:
        Exception: If an error is encountered writing the file.
    """
    defaults = BuilderUtils.read_yaml_file(defaults_file)
    component_spec['implementation']['container']['image'] = (
        f'''{defaults['gcp']['af_registry_location']}-docker.pkg.dev/'''
        f'''{defaults['gcp']['project_id']}/'''
        f'''{defaults['gcp']['af_registry_name']}/'''
        f'''components/component_base:latest''')
    component_spec['implementation']['container']['command'] = [
        'python3',
        f'''/pipelines/component/src/{component_spec['name']+'.py'}''']
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
    # Todo:
    # Figure out what to do with package_to_install
    name = func.__name__
    parsed_docstring = docstring_parser.parse(inspect.getdoc(func))
    description = parsed_docstring.short_description
    # make yaml
    component_spec = {}
    component_spec['name'] = name
    if description:
        component_spec['description'] = description
    component_spec['inputs'] = get_function_parameters(func)
    component_spec['implementation'] = {}
    component_spec['implementation']['container'] = {}
    component_spec['implementation']['container']['image'] = 'TBD'
    component_spec['implementation']['container']['command'] = get_packages_to_install_command(func, packages_to_install)
    component_spec['implementation']['container']['args'] = ['--executor_input',
        {'executorInput': None}, '--function_to_execute', name]
    filename = BuilderUtils.TMPFILES_DIR + f'/{name}.yaml'
    BuilderUtils.make_dirs([BuilderUtils.TMPFILES_DIR]) # if it doesn't already exist
    BuilderUtils.write_yaml_file(filename, component_spec, 'w')

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
    concat_package_list = ' '.join(
        [repr(str(package)) for package in packages_to_install])
    # pylint: disable=anomalous-backslash-in-string
    install_python_packages_script = (
    f'''if ! [ -x "$(command -v pip)" ]; then{newline}'''
    f'''    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip{newline}'''
    f'''fi{newline}'''
    f'''PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \{newline}'''
    f'''    --no-warn-script-location {concat_package_list} && "$0" "$@"{newline}'''
    f'''{newline}''')
    src_code = BuilderUtils.get_function_source_definition(func)
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
    return BuilderUtils.update_params(parameter_holder)

def maybe_strip_optional_from_annotation(annotation: T) -> T:
    """Strips 'Optional' from 'Optional[<type>]' if applicable.
    For example::
      Optional[str] -> str
      str -> str
      List[int] -> List[int]
    Args:
      annotation: The original type annotation which may or may not has
        `Optional`.
    Returns:
      The type inside Optional[] if Optional exists, otherwise the original type.
    """
    if getattr(annotation, '__origin__',
               None) is Union and annotation.__args__[1] is type(None):
        return annotation.__args__[0]
    return annotation
