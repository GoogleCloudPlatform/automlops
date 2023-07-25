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

# pylint: disable=C0103
# pylint: disable=line-too-long

import inspect
import os
import subprocess

import itertools
import textwrap
from typing import Callable
import yaml

from AutoMLOps.utils.constants import (
    CACHE_DIR,
    PLACEHOLDER_IMAGE
)

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
        raise yaml.YAMLError(f'Error reading file. {err}') from err
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
        raise yaml.YAMLError(f'Error writing to file. {err}') from err

def read_file(filepath: str) -> str:
    """Reads a file and returns contents as a string.
       Defaults to utf-8 encoding.

    Args:
        filepath: Path to the file.
    Returns:
        str: Contents of the file.
    Raises:
        Exception: If an error is encountered reading the file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            contents = file.read()
        file.close()
    except FileNotFoundError as err:
        raise FileNotFoundError(f'Error reading file. {err}') from err
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
        raise OSError(f'Error writing to file. {err}') from err

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
        raise OSError(f'Error chmod-ing file. {err}') from err

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
    """Reads yamls in the cache directory, verifies they are component
       yamls, and returns the name of the files.

    Args:
        full_path: Boolean; if false, stores only the filename w/o extension.
    Returns:
        list: Contains the names or paths of all component yamls in the dir.
    """
    components_list = []
    elements = os.listdir(CACHE_DIR)
    for file in list(filter(lambda y: ('.yaml' or '.yml') in y, elements)):
        path = os.path.join(CACHE_DIR, file)
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
        subprocess.run([command],
                       shell=True,
                       check=True,
                       stdout=stdout,
                       stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f'Error executing process. {err}') from err

def validate_schedule(schedule_pattern: str, run_local: str):
    """Validates that the inputted schedule parameter aligns with the run_local configuration.
    Note: this function does not validate that schedule_pattern is a properly formatted cron value.
    Cron format validation is done in the backend by GCP.
    
    Args:
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    Raises:
        Exception: If schedule is not cron formatted or run_local validation fails.
    """
    if schedule_pattern != 'No Schedule Specified' and run_local:
        raise ValueError('run_local must be set to False to use Cloud Scheduler.')

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
        list: 'JsonArray',
        dict: 'JsonObject'
    }
    for param in params:
        try:
            param['type'] = python_kfp_types_mapper[param['type']]
        except KeyError as err:
            raise ValueError(f'Unsupported python type - we only support '
                             f'primitive types at this time. {err}') from err
    return params

def get_function_source_definition(func: Callable) -> str:
    """Returns a formatted string of the source code.

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
    Returns:
        str: The source code from the inputted function.
    Raises:
        Exception: If the preprocess operates failed.
    """
    source_code = inspect.getsource(func)
    source_code = textwrap.dedent(source_code)
    source_code_lines = source_code.split('\n')
    source_code_lines = itertools.dropwhile(lambda x: not x.startswith('def'),
                                            source_code_lines)
    if not source_code_lines:
        raise ValueError(
            f'Failed to dedent and clean up the source of function "{func.__name__}". '
            f'It is probably not properly indented.')

    return '\n'.join(source_code_lines)

def format_spec_dict(job_spec: dict) -> str:
    """Takes in a job spec dictionary and removes the quotes around the component op name. 
    e.g. 'component_spec': 'train_model' becomes 'component_spec': train_model.
    This is necessary to in order for the op to be callable within the Python code.

    Args:
        job_spec: Dictionary with job spec info.

    Returns:
        str: Python formatted dictionary code.
    """
    quote = '\''
    left_bracket = '{'
    right_bracket = '}'
    newline = '\n'

    return (
        f'''{left_bracket}\n'''
        f'''    {f'{newline}    '.join(f"   {quote}{k}{quote}: {quote if k != 'component_spec' else ''}{v}{quote if k != 'component_spec' else ''}," for k, v in job_spec.items())}{newline}'''
        f'''    {right_bracket}\n''')

def is_using_kfp_spec(image: str):
    """Takes in an image string from a component yaml and determines if it came from kfp or not.

    Args:
        image: image string.

    Returns:
        bool: is the component using kfp spec.
    """
    return image != PLACEHOLDER_IMAGE
