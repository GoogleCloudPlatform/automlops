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

"""Unit tests for utils module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

import os
import pytest
import yaml
from contextlib import nullcontext as does_not_raise
import pandas as pd
 

from AutoMLOps.utils.utils import (
    delete_file,
    make_dirs,
    read_file,
    read_yaml_file,
    write_and_chmod,
    write_file,
    write_yaml_file,
    get_components_list,
    is_component_config,
    execute_process, 
    validate_schedule,
    update_params,
    get_function_source_definition,
    format_spec_dict
)
import AutoMLOps.utils.utils

def test_make_dirs():
    """Tests AutoMLOps.utils.utils.make_dirs, which creates a list of directories
    if they do not already exist."""
    # Create a list of directories to create.
    directories = ['dir1', 'dir2']

    # Call the `make_dirs` function.
    make_dirs(directories)

    # Assert that the directories were created.
    for directory in directories:
        assert os.path.exists(directory)
        os.rmdir(directory)

def test_make_dirs_with_same_name():
    """Tests AutoMLOps.utils.utils.make_dirs, which creates a list of directories
    if they do not already exist. Checks how same directory names are handled."""
    # Create a list of directories to create.
    directories = ['dir1', 'dir1']

    # Call the `make_dirs` function.
    make_dirs(directories)

    # Assert that the directories were created and a duplicate does not exist.
    assert os.path.exists(directories[0])
    os.rmdir('dir1')
    assert not os.path.exists(directories[1])

def test_make_dirs_invalid_dir_names():
    """Tests AutoMLOps.utils.utils.make_dirs, which creates a list of directories
    if they do not already exist."""
    # Create a list of directories to create, including the invalid name.
    directories = ['dir1', '\0']

    # Call the `make_dirs` function and expect ValueError.
    with pytest.raises(ValueError):
        make_dirs(directories)


def test_read_yaml_file():
    """Tests AutoMLOps.utils.utils.read_yaml_file, which reads a yaml file and 
    returns the file contents as a dict."""
    # Create a yaml file.
    with open('test.yaml', 'w', encoding='utf-8') as file:
        yaml.dump({'key1': 'value1', 'key2': 'value2'}, file)

    # Call the `read_yaml_file` function.
    file_dict = read_yaml_file('test.yaml')

    # Assert that the file_dict contains the expected values.
    assert file_dict == {'key1': 'value1', 'key2': 'value2'}

    # Remove test file
    os.remove('test.yaml')

def test_read_invalid_yaml_file():
    """Tests AutoMLOps.utils.utils.read_yaml_file with invalid syntax, which reads a yaml file and 
    returns the file contents as a dict."""
    # Create a yaml file.
    with open('test.yaml', 'w', encoding='utf-8') as file:
        yaml.dump({'key1': 'value1', False: 'random stuff'}, file)
        yaml.dump(r"-A fails", file)

    # Call the `read_yaml_file` function.
    with pytest.raises(yaml.YAMLError):
        read_yaml_file('test.yaml')
        
    # Remove test file
    os.remove('test.yaml')

def test_write_yaml_file():
    """Tests AutoMLOps.utils.utils.write_yaml_file, which writes a yaml file."""
    # Call the `write_yaml_file` function.
    write_yaml_file('test.yaml', {'key1': 'value1', 'key2': 'value2'}, 'w')

    # Assert that the file contains the expected values.
    with open('test.yaml', 'r', encoding='utf-8') as file:
        file_dict = yaml.safe_load(file)
    assert file_dict == {'key1': 'value1', 'key2': 'value2'}

    # Remove test file
    os.remove('test.yaml')

def test_write_yaml_file_invalid_filepath():
    """Tests AutoMLOps.utils.utils.write_yaml_file, which writes a yaml file inputting an invalid filepath."""
    # Call the `write_yaml_file` function.
    with pytest.raises(FileNotFoundError):
        write_yaml_file('/nonexistent/directory', {'key1': 'value1', 'key2': 'value2'}, 'w') 

def test_write_yaml_file_invalid_mode():
    """Tests AutoMLOps.utils.utils.write_yaml_file, which writes a yaml file. Input an invalid mode expecting an IOError."""
    # Call the `write_yaml_file` function with an invalid mode.
    with pytest.raises(IOError):
        write_yaml_file('test.yaml', {'key1': 'value1', 'key2': 'value2'}, 'r')

def test_read_file():
    """Tests AutoMLOps.utils.utils.read_file, which writes a dictionary to a yaml file."""
    # Create a file.
    with open('test.txt', 'w', encoding='utf-8') as file:
        file.write('This is a test file.')

    # Call the `read_file` function.
    contents = read_file('test.txt')

    # Assert that the contents of the file are correct.
    assert contents == 'This is a test file.'

    # Remove test file
    os.remove('test.txt')

def test_read_file_invalid_path():
    """Tests AutoMLOps.utils.utils.read_file, which writes a dictionary to a yaml file. Expects FileError from passing invalid filepath"""
    # Call the `read_file` function with nonexistent file and expect FileNotFound Error.
    with pytest.raises(FileNotFoundError):
        read_file('fail') 

def test_write_file():
    """Tests AutoMLOps.utils.utils.write_file, which writes a file at the specified path."""
    # Create a file.
    open('test.txt', 'w', encoding='utf-8')

    # Call the `write_file` function.
    write_file('test.txt', 'This is a test file.', 'w')

    # Assert that the file exists.
    assert os.path.exists('test.txt')

    # Assert that the contents of the file are correct.
    with open('test.txt', 'r', encoding='utf-8') as file:
        contents = file.read()
    assert contents == 'This is a test file.'

    # Remove test file
    os.remove('test.txt')

    
def test_write_file_invalid_path():
    """Tests AutoMLOps.utils.utils.write_file, which writes a file at the specified path.
    Expect OSError passing an invalid filepath."""
    # Call the `write_file` function with an invalid file path.
    with pytest.raises(OSError):
        write_file(15, 'This is a test file.', 'w')

def test_write_and_chmod():
    """Tests AutoMLOps.utils.utils.write_and_chmod, which writes a file at the specified path
    and chmods the file to allow for execution"""
    # Create a file.
    with open('test.txt', 'w', encoding='utf-8') as file:
        file.write('This is a test file.')

    # Call the `write_and_chmod` function.
    write_and_chmod('test.txt', 'This is a test file.')

    # Assert that the file exists and is executable.
    assert os.path.exists('test.txt')
    assert os.access('test.txt', os.X_OK)

    # Assert that the contents of the file are correct.
    with open('test.txt', 'r', encoding='utf-8') as file:
        contents = file.read()
    assert contents == 'This is a test file.'

    # Delete the file.
    os.remove('test.txt')

def test_delete_file():
    """Tests AutoMLOps.utils.utils.delete_file, which deletes a file at the specified path."""
    # Create a file.
    with open('test.txt', 'w', encoding='utf-8') as file:
        file.write('This is a test file.')

    # Call the `delete_file` function.
    delete_file('test.txt')

    # Assert that the file does not exist.
    assert not os.path.exists('test.txt')

def test_get_components_list(mocker):
    """Tests the get_components_list function, which reads yamls in tmpfiles directory,
    verifies they are component yamls, and returns the name of the files."""
    # Patch tmpfiles directory with the cwd
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')

    # Create a component YAML file.
    with open("component.yaml", "w") as f:
        yaml.dump({'name': 'value1', 'inputs': 'value2', 'implementation': 'value3'}, f)

    # Assert that the returned list contains the expected path.
    assert get_components_list(full_path=False) == ["component"]
    assert get_components_list(full_path=True) == [os.path.join(".", "component.yaml")]

    # Delete the temporary directory.
    os.remove('component.yaml')

def test_get_components_list_empty(mocker):
    """Tests the get_components_list function, which reads yamls in tmpfiles directory,
    verifies they are component yamls, and returns the name of the files. Verifies an empty list comes back if no YAMLs are present."""

    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')
    assert get_components_list(full_path=False) == []

def test_get_components_list_invalid_dir():
    """Tests the get_components_list function, which reads yamls in tmpfiles directory,
    verifies they are component yamls, and returns the name of the files. Call function with a nonexistent dir, expecting OSError."""

    # Create a component YAML file.
    with open("component.yaml", "w") as f:
        yaml.dump({'name': 'value1', 'inputs': 'value2', 'implementation': 'value3'}, f)

    # Assert that calling get_components_list with an invalid directory raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        get_components_list(full_path=False) == ["component"]

    # Delete the temporary directory.
    os.remove('component.yaml')


@pytest.mark.parametrize(
    'yaml_contents, expected',
    [
        (
            {
                'name': 'value1',
                'inputs': 'value2', 
                'implementation': 'value3'
            }, 
            True),
        (
            {
                'name': 'value1', 
                'inputs': 'value2'
            },
            False)
    ]
)
def test_is_component_config(yaml_contents, expected):
    """Tests the is_component_config function, which checks to see if the given file is
    a component yaml."""
    with open("component.yaml", "w") as f:
        yaml.dump(yaml_contents, f)
    assert expected == is_component_config("component.yaml")
    os.remove("component.yaml")

def test_execute_process():
    """Tests execute_process function, which executes an external shell process."""
    execute_process('touch test.txt', to_null=False)
    assert os.path.exists('test.txt')
    os.remove('test.txt')

def test_execute_process_invalid_command(): 
    """Tests execute_process function, which executes an external shell process. Runs an invalid command, expecting error."""
    with pytest.raises(RuntimeError):
        execute_process('not a real command', to_null=False)

@pytest.mark.parametrize(
    'sch_pattern, run_loc, raises_error',
    [
        ('No Schedule Specified', True, False), 
        ('No Schedule Specified', False, False), 
        ('Schedule', True, True), 
        ('Schedule', False, False)
    ])
def test_validate_schedule(sch_pattern, run_loc, raises_error):
    """ Tests validate_schedule function, which validates the inputted schedule parameter."""
    if raises_error:
        with pytest.raises(ValueError):
            validate_schedule(schedule_pattern=sch_pattern, run_local=run_loc)
    else:
        assert validate_schedule(schedule_pattern=sch_pattern, run_local=run_loc) is None

@pytest.mark.parametrize("params, expected", [
    ([{'name': 'param1', 'type': int}], [{'name': 'param1', 'type': 'Integer'}]),
    ([{'name': 'param2', 'type': str}], [{'name': 'param2', 'type': 'String'}]),
    ([{'name': 'param3', 'type': float}], [{'name': 'param3', 'type': 'Float'}]),
    ([{'name': 'param4', 'type': bool}], [{'name': 'param4', 'type': 'Bool'}]),
    ([{'name': 'param5', 'type': list}], [{'name': 'param5', 'type': 'List'}]),
    ([{'name': 'param6', 'type': dict}], [{'name': 'param6', 'type': 'Dict'}]),
    ([{'name': 'param6', 'type': pd.DataFrame}], None)
])
def test_update_params(params, expected):
    """Tests the update_params function, which reformats the source code type labels as strings."""
    if expected is not None:
        assert expected == update_params(params)
    else:
        with pytest.raises(ValueError):
            assert update_params(params)

def func1(x):
    return x + 1
def func2(x, y):
    return x + y
def func3(x, y, z):
    return x + y + z
def func4():
    def inner_func():
        res = 1+1
    return inner_func()

@pytest.mark.parametrize("func, expected", [
    (func1, "def func1(x):\n    return x + 1\n"),
    (func2, "def func2(x, y):\n    return x + y\n"),
    (func3, "def func3(x, y, z):\n    return x + y + z\n"),
    (func4, "def func4():\n    def inner_func():\n        res = 1+1\n    return inner_func()\n")
])
def test_get_function_source_definition(func, expected):
    """Tests the get_function_source_definition function, which returns a formatted string
    of the source code."""
    assert expected == get_function_source_definition(func)

@pytest.mark.parametrize("job_spec, expected", [
    ({"component_spec": "train_model"}, "{\n       'component_spec': train_model,\n    }\n"),
    ({"component_spec": "train_model", "other_spec": "other_value"}, "{\n       'component_spec': train_model,\n       'other_spec': 'other_value',\n    }\n"),
    ({}, "{\n    \n    }\n"), 
    ({"{": "}"},"{\n       '{': '}',\n    }\n" )
])
def test_format_spec_dict(job_spec, expected):
    """Tests the format_spec_dict function, which takes in a spec dictionary and removes the quotes
    around the component op name."""

    # Format the spec dict.
    formatted_spec = format_spec_dict(job_spec)

    # Assert that the formatted spec is equal to the expected value.
    assert formatted_spec == expected