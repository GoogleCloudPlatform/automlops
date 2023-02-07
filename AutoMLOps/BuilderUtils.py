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

"""Utility functions and globals to be used by all
   other modules in this directory."""

import os
import subprocess
import yaml

# pylint: disable=line-too-long
TMPFILES_DIR = '.tmpfiles'
IMPORTS_TMPFILE = f'{TMPFILES_DIR}/imports.py'
CELL_TMPFILE = f'{TMPFILES_DIR}/cell.py'
PIPELINE_TMPFILE = f'{TMPFILES_DIR}/pipeline_scaffold.py'
PARAMETER_VALUES_PATH = 'pipelines/runtime_parameters/pipeline_parameter_values.json'
PIPELINE_JOB_SPEC_PATH = 'scripts/pipeline_spec/pipeline_job.json'
LICENSE = (
    '# Licensed under the Apache License, Version 2.0 (the "License");\n'
    '# you may not use this file except in compliance with the License.\n'
    '# You may obtain a copy of the License at\n'
    '#\n'
    '#     http://www.apache.org/licenses/LICENSE-2.0\n'
    '#\n'
    '# Unless required by applicable law or agreed to in writing, software\n'
    '# distributed under the License is distributed on an "AS IS" BASIS,\n'
    '# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n'
    '# See the License for the specific language governing permissions and\n'
    '# limitations under the License.\n'
    '#\n'
    '# DISCLAIMER: This code is generated as part of the AutoMLOps output.\n'
    '\n')

def make_dirs(directories: list):
    """Makes directories with the specified names.

    Args:
        directories: Path of the directories to make.
    """
    for d in directories:
        try:
            os.makedirs(d)
        except FileExistsError:
            pass

def read_yaml_file(filepath: str) -> dict:
    """Reads a yaml and returns file contents as a dict.
       Defaults to utf-8 encoding.

    Args:
        filepath: Path to the yaml.
    Returns:
        dict: Contents of the yaml.
    Raises:
        Exception: If an error is encountered reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            file_dict = yaml.safe_load(file)
        file.close()
    except yaml.YAMLError as err:
        raise Exception(f'Error reading file. {err}') from err
    return file_dict

def write_yaml_file(filepath: str, contents: dict, mode: str):
    """Writes a dictionary to yaml. Defaults to utf-8 encoding.

    Args:
        filepath: Path to the file.
        contents: Dictionary to be written to yaml.
        mode: Read/write mode to be used.
    Raises:
        Exception: If an error is encountered writing the file.
    """
    try:
        with open(filepath, mode, encoding='utf-8') as file:
            yaml.safe_dump(contents, file, sort_keys=False)
        file.close()
    except yaml.YAMLError as err:
        raise Exception(f'Error writing to file. {err}') from err

def read_file(filepath: str) -> str:
    """Reads a file and returns contents as a string.
       Defaults to utf-8 encoding.

    Args:
        filepath: Path to the yaml.
    Returns:
        dict: Contents of the yaml.
    Raises:
        Exception: If an error is encountered reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            contents = file.read()
        file.close()
    except FileNotFoundError as err:
        raise Exception(f'Error reading file. {err}') from err
    return contents

def write_file(filepath: str, text: str, mode: str):
    """Writes a file at the specified path. Defaults to utf-8 encoding.

    Args:
        filepath: Path to the file.
        text: Text to be written to file.
        mode: Read/write mode to be used.
    Raises:
        Exception: If an error is encountered writing the file.
    """
    try:
        with open(filepath, mode, encoding='utf-8') as file:
            file.write(text)
        file.close()
    except OSError as err:
        raise Exception(f'Error writing to file. {err}') from err

def write_and_chmod(filepath: str, text: str):
    """Writes a file at the specified path and chmods the file
       to allow for execution.

    Args:
        filepath: Path to the file.
        text: Text to be written to file.
    Raises:
        Exception: If an error is encountered chmod-ing the file.
    """
    write_file(filepath, text, 'w+')
    try:
        st = os.stat(filepath)
        os.chmod(filepath, st.st_mode | 0o111)
    except OSError as err:
        raise Exception(f'Error chmod-ing file. {err}') from err

def delete_file(filepath: str):
    """Deletes a file at the specified path.
       If it does not exist, pass.

    Args:
        filepath: Path to the file.
    """
    try:
        os.remove(filepath)
    except OSError:
        pass

def get_components_list(full_path: bool = True) -> list:
    """Reads yamls in tmpfiles directory, verifies they are component
       yamls, and returns the name of the files.

    Args:
        full_path: Boolean; if false, stores only the filename w/o extension.
    Returns:
        list: Contains the names or paths of all component yamls in the dir.
    """
    components_list = []
    elements = os.listdir(TMPFILES_DIR)
    for file in list(filter(lambda y: ('.yaml' or '.yml') in y, elements)):
        path = os.path.join(TMPFILES_DIR, file)
        if is_component_config(path):
            if full_path:
                components_list.append(path)
            else:
                components_list.append(os.path.basename(file).split('.')[0])
    return components_list

def is_component_config(filepath: str) -> bool:
    """Checks to see if the given file is a component yaml.

    Args:
        filepath: Path to a yaml file.
    Returns:
        bool: Whether the given file is a component yaml.
    """
    required_keys = ['name','inputs','implementation']
    file_dict = read_yaml_file(filepath)
    return all(key in file_dict.keys() for key in required_keys)

def execute_process(command: str, to_null: bool):
    """Executes an external shell process.

    Args:
        command: The string of the command to execute.
        to_null: Determines where to send output.
    Raises:
        Exception: If an error occurs in executing the script.
    """
    stdout = subprocess.DEVNULL if to_null else None
    try:
        subprocess.run([command], shell=True, check=True,
            stdout=stdout,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        raise Exception(f'Error executing process. {err}') from err

def validate_schedule(schedule_pattern: str, run_local: str):
    """Validates that the inputted schedule parameter.

    Args:
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    Raises:
        Exception: If schedule is not cron formatted or run_local validation fails.
    """
    if schedule_pattern != 'No Schedule Specified' and run_local:
        raise Exception('run_local must be set to False to use Cloud Scheduler.')

def validate_name(name: str):
    """Validates that the inputted name parameter is of type str.

    Args:
        name: The name of a component or pipeline.
    Raises:
        Exception: If the name is not of type str.
    """
    if not isinstance(name, str):
        raise Exception('Pipeline and Component names must be of type string.')

def validate_params(params: list):
    """Verifies that the inputted params follow the correct
       specification.

    Args:
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
    Raises:
        Exception: If incorrect params specification.
    """
    s = set()
    for param in params:
        try:
            name = param['name']
            if not isinstance(name, str):
                raise Exception('Parameter name must be of type string.')
            param_type = param['type']
            if not isinstance(param_type, type):
                raise Exception('Parameter type must be a valid python type.')
        except KeyError as err:
            raise Exception(f'Parameter {param} does not contain '
                            f'required keys. {err}') from err
        if param['name'] in s:
            raise Exception(f'''Duplicate parameter {param['name']} found.''')
        else:
            s.add(param['name'])
        if 'description' not in param.keys():
            param['description'] = 'No description provided.'

def validate_pipeline_structure(pipeline: list):
    """Verifies that the pipeline follows the correct
       specification.

    Args:
        pipeline: Defines the components to use in the pipeline,
            their order, and a mapping of component params to
            pipeline params. A list of dictionaries, each dict
            specifies a custom component and contains keys:
                'component_name': name of the component
                'param_mapping': a list of tuples mapping ->
                    (component_param, pipeline_param)
    Raises:
        Exception: If incorrect pipeline specification.
    """
    components_list = get_components_list(full_path=False)
    for component in pipeline:
        try:
            component_name = component['component_name']
            if component_name not in components_list:
                raise Exception(f'Component {component_name} not found - '
                    f'No matching yaml definition in tmpfiles directory.')
            param_mapping = component['param_mapping']
        except KeyError as err:
            raise Exception(f'Component {component} does not contain '
                f'required keys. {err}') from err
        for param_tuple in param_mapping:
            if not isinstance(param_tuple, tuple):
                raise Exception(f'Mapping contains a non-tuple '
                                f'element {param_tuple}')
            elif len(param_tuple) != 2:
                raise Exception(f'Mapping must contain only 2 elements, '
                                f'tuple {param_tuple} is invalid.')
            else:
                for item in param_tuple:
                    if not isinstance(item, str):
                        raise Exception(f'Mapping must be str-str, '
                                        f'tuple {param_tuple} is invalid.')

def update_params(params: list) -> list:
    """Converts the parameter types from Python types
       to Kubeflow types. Currently only supports
       Python primitive types.

    Args:
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
    Returns:
        list: Params list with converted types.
    Raises:
        Exception: If an inputted type is not a primitive.
    """
    python_kfp_types_mapper = {
        int: 'Integer',
        str: 'String',
        float: 'Float',
        bool: 'Bool',
        list: 'List',
        dict: 'Dict'
    }
    for param in params:
        try:
            param['type'] = python_kfp_types_mapper[param['type']]
        except KeyError as err:
            raise Exception(f'Unsupported python type - we only support '
                            f'primitive types at this time. {err}') from err
    return params
