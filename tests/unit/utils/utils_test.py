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

from contextlib import nullcontext as does_not_raise
import os
from typing import Callable, List

import pandas as pd
import pytest
import pytest_mock
import yaml

import google_cloud_automlops.utils.utils
from google_cloud_automlops.utils.utils import (
    delete_file,
    execute_process,
    get_components_list,
    get_function_source_definition,
    is_component_config,
    make_dirs,
    read_file,
    read_yaml_file,
    stringify_job_spec_list,
    update_params,
    validate_schedule,
    write_and_chmod,
    write_file,
    write_yaml_file
)


# Define simple functions to be used in tests
def func1(x):
    return x + 1


def func2(x, y):
    return x + y


def func3(x, y, z):
    return x + y + z


def func4():

    def inner_func():
        res = 1 + 1
        return res

    return inner_func()


@pytest.mark.parametrize(
    'directories, existance, expectation',
    [
        (['dir1', 'dir2'], [True, True], does_not_raise()),
        (['dir1', 'dir1'], [True, False], does_not_raise()),
        (['\0', 'dir1'], [True, True], pytest.raises(ValueError))
    ]
)
def test_make_dirs(directories: List[str], existance: List[bool], expectation):
    """Tests make_dirs, which creates a list of directories if they do not
    already exist. There are three test cases for this function:
        1. Expected outcome, folders created as expected.
        2. Duplicate folder names given, expecting only one folder created.
        3. Invalid folder name given, expects an error.

    Args:
        directories (List[str]): List of directories to be created.
        existance (List[bool]): List of booleans indicating whether the listed directories to
            be created are expected to exist after invoking make_dirs.
        expectation: Any corresponding expected errors for each set of parameters.
    """
    with expectation:
        make_dirs(directories=directories)
        for directory, exist in zip(directories, existance):
            assert os.path.exists(directory) == exist
            if exist:
                os.rmdir(directory)


@pytest.mark.parametrize(
    'filepath, content1, content2, expectation',
    [
        (
            'test.yaml',
            {'key1': 'value1', 'key2': 'value2'},
            None,
            does_not_raise()
        ),
        (
            'test.yaml',
            {'key1': 'value1', False: 'random stuff'},
            r'-A fails',
            pytest.raises(yaml.YAMLError)
        )
    ]
)
def test_read_yaml_file(filepath: str, content1: dict, content2: str, expectation):
    """Tests read_yaml_file, which reads a yaml file and returns the file
    contents as a dict. There are two sets of test cases for this function:
        1. Expected outcome, file read in with correct content.
        2. File to be read is not in standard yaml format, expects a yaml error.

    Args:
        filepath (str): Path to yaml file to be read.
        content1 (dict): First set of content to be included in the yaml at the given
            file path.
        content2 (str): Second set of content to be included in the yaml at the given
            file path.
        expectation: Any corresponding expected errors for each set of
            parameters.
    """
    with open(file=filepath, mode='w', encoding='utf-8') as file:
        if content1:
            yaml.dump(content1, file)
        if content2:
            yaml.dump(content2, file)
    with expectation:
        assert read_yaml_file(filepath=filepath) == content1
    os.remove(path=filepath)


@pytest.mark.parametrize(
    'filepath, mode, expectation',
    [
        ('test.yaml', 'w', does_not_raise()),
        ('/nonexistent/directory', 'w',  pytest.raises(FileNotFoundError)),
        ('test.yaml', 'r', pytest.raises(IOError))
    ]
)
def test_write_yaml(filepath: str, mode: str, expectation):
    """Tests write_yaml_file, which writes a yaml file. There are three sets of
    test cases for this function:
        1. Expected outcome, yaml is written correctly.
        2. Invalid file path given, expecting a FileNotFoundError.
        3. Invalid mode given, expecting an IOError.

    Args:
        filepath (str): Path for yaml file to be written.
        mode (str): Read/write mode to be used.
        expectation: Any corresponding expected errors for each set of
            parameters.
    """
    contents = {'key1': 'value1', 'key2': 'value2'}
    with expectation:
        write_yaml_file(
            filepath=filepath,
            contents=contents,
            mode=mode
        )
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            assert yaml.safe_load(file) == contents
        os.remove(path=filepath)


@pytest.mark.parametrize(
    'filepath, text, write_file_bool, expectation',
    [
        ('test.txt', 'This is a text file.', True, does_not_raise()),
        ('fail', '', False, pytest.raises(FileNotFoundError))
    ]
)
def test_read_file(filepath: str, text: str, write_file_bool: bool, expectation):
    """Tests read_file, which reads a text file in as a string. There are two
    sets of test cases for this function:
        1. Expected outcome, file is read correctly.
        2. Invalid file path given (file was not written), expecting a
            FileNotFoundError.

    Args:
        filepath (str): Path for file to be read from.
        text (str): Text expected to be read from the given file.
        write_file_bool (bool): Whether or not the file should be written for this
            test case.
        expectation: Any corresponding expected errors for each set of
            parameters.
    """
    if write_file_bool:
        with open(file=filepath, mode='w', encoding='utf-8') as file:
            file.write(text)
    with expectation:
        assert read_file(filepath=filepath) == text
    if os.path.exists(filepath):
        os.remove(filepath)


@pytest.mark.parametrize(
    'filepath, text, mode, expectation',
    [
        ('test.txt', 'This is a test file.', 'w', does_not_raise()),
        (15, 'This is a test file.', 'w', pytest.raises(OSError))
    ]
)
def test_write_file(filepath: str, text: str, mode: str, expectation):
    """Tests write_file, which writes a string to a text file. There are two
    test cases for this function:
        1. Expected outcome, file is written as expected.
        2. Invalid file path given (file was not written), expecting
            an OSError.

    Args:
        filepath (str): Path for file to be written.
        text (str): Content to be written to the file at the given filepath.
        mode (str): Read/write mode to be used.
        expectation: Any corresponding expected errors for each set of
            parameters.
    """
    with expectation:
        write_file(
            filepath=filepath,
            text=text,
            mode=mode
        )
        assert os.path.exists(filepath)
        with open(file=filepath, mode='r', encoding='utf-8') as file:
            assert text == file.read()
        os.remove(filepath)


def test_write_and_chmod():
    """Tests write_and_chmod, which writes a file at the specified path
    and chmods the file to allow for execution.
    """
    # Create a file.
    with open(file='test.txt', mode='w', encoding='utf-8') as file:
        file.write('This is a test file.')

    # Call the `write_and_chmod` function.
    write_and_chmod('test.txt', 'This is a test file.')

    # Assert that the file exists and is executable.
    assert os.path.exists('test.txt')
    assert os.access('test.txt', os.X_OK)

    # Assert that the contents of the file are correct.
    with open(file='test.txt', mode='r', encoding='utf-8') as file:
        contents = file.read()
    assert contents == 'This is a test file.'
    os.remove('test.txt')


@pytest.mark.parametrize(
    'file_to_delete, valid_file',
    [
        ('test.txt', True),
        ('fake.txt', False)
    ]
)
def test_delete_file(file_to_delete: str, valid_file: bool):
    """Tests delete_file, which deletes a file at the specified path.
    There are two test cases for this function:
        1. Create a valid file and call delete_file, which is expected to successfully delete the file.
        2. Pass in a nonexistent file and call delete_file, which is expected to pass.

    Args:
        file_to_delete (str): Name of file to delete.
        valid_file (bool): Whether or not the file to delete actually exists."""
    if not valid_file:
        with does_not_raise():
            delete_file(file_to_delete)
    else:
        with open(file=file_to_delete, mode='w', encoding='utf-8') as file:
            file.write('This is a test file.')
            delete_file(file_to_delete)
            assert not os.path.exists(file_to_delete)


@pytest.mark.parametrize(
    'comp_path, comp_name, patch_cwd, expectation',
    [
        (['component.yaml'], ['component'], True, does_not_raise()),
        ([], [], True, does_not_raise()),
        (['component.yaml'], ['component'], False, pytest.raises(FileNotFoundError))
    ]
)
def test_get_components_list(mocker: pytest_mock.MockerFixture,
                             comp_path: List[str],
                             comp_name: List[str],
                             patch_cwd: bool,
                             expectation):
    """Tests get_components_list, which reads yamls in .AutoMLOps-cache directory,
    verifies they are component yamls, and returns the name of the files. There
    are three test cases for this function:
        1. Expected outcome, component list is pulled as expected.
        2. Verifies an empty list comes back if no YAMLs are present.
        3. Call function with a nonexistent dir, expecting OSError.

    Args:
        mocker: Mocker to patch the cache directory for component files.
        comp_path (List[str]): Path(s) to component yamls.
        comp_name (List[str]): Name(s) of components.
        patch_cwd (bool): Boolean flag indicating whether to patch the current working
            directory from CACHE_DIR to root
        expectation: Any corresponding expected errors for each set of
            parameters.
    """
    if patch_cwd:
        mocker.patch.object(google_cloud_automlops.utils.utils, 'CACHE_DIR', '.')
    if comp_path:
        for file in comp_path:
            with open(file=file, mode='w', encoding='utf-8') as f:
                yaml.dump(
                    {
                        'name': 'value1', 
                        'inputs': 'value2',
                        'implementation': 'value3'
                    },
                    f)
    with expectation:
        assert get_components_list(full_path=False) == comp_name
        assert get_components_list(full_path=True) == [os.path.join('.', file) for file in comp_path]
    for file in comp_path:
        if os.path.exists(file):
            os.remove(file)


@pytest.mark.parametrize(
    'yaml_contents, expectation',
    [
        (
            {
                'name': 'value1',
                'inputs': 'value2',
                'implementation': 'value3'
            },
            True
        ),
        (
            {
                'name': 'value1',
                'inputs': 'value2'
            },
            False
        )
    ]
)
def test_is_component_config(yaml_contents: dict, expectation: bool):
    """Tests is_component_config, which which checks to see if the given file is
    a component yaml. There are two test cases for this function:
        1. A valid component is given, expecting return value True.
        2. An invalid component is given, expecting return value False.

    Args:
        yaml_contents (dict): Component configurations to be written to yaml file.
        expected (bool): Expectation of whether or not the configuration is valid.
    """
    with open(file='component.yaml', mode='w', encoding='utf-8') as f:
        yaml.dump(yaml_contents, f)
    assert expectation == is_component_config('component.yaml')
    os.remove('component.yaml')


@pytest.mark.parametrize(
    'command, to_null, expectation',
    [
        ('touch test.txt', False, False),
        ('not a real command', False, True),
        ('echo "howdy"', True, False)
    ]
)
def test_execute_process(command: str, to_null: bool, expectation: bool):
    """Tests execute_process, which executes an external shell process. There
    are two test cases for this function:
        1. A valid command to create a file, which is expected to run successfully.
        2. An invalid command, which is expected to raise a RunTime Error.
        3. A valid command to output a string, which is expected to send output to null

    Args:
        command (str): Command that is to be executed.
        expectation (bool): Whether or not an error is expected to be raised.
    """
    if expectation:
        with pytest.raises(RuntimeError):
            execute_process(command=command, to_null=to_null)
    elif to_null:
        assert execute_process(command=command, to_null=to_null) is None
    else:
        execute_process(command=command, to_null=to_null)
        assert os.path.exists('test.txt')
        os.remove('test.txt')


@pytest.mark.parametrize(
    'sch_pattern, use_ci, expectation',
    [
        ('No Schedule Specified', True, does_not_raise()),
        ('No Schedule Specified', False, does_not_raise()),
        ('Schedule', False, pytest.raises(ValueError)),
        ('Schedule', True, does_not_raise())
    ]
)
def test_validate_schedule(sch_pattern: str, use_ci: bool, expectation):
    """Tests validate_schedule, which validates the inputted schedule
    parameter. There are four test cases for this function, which tests each
    combination of sch_pattern and run_loc for the expected results.

    Args:
        sch_pattern (str): Cron formatted value used to create a Scheduled retrain job.
        use_ci (bool): Flag that determines whether to use Cloud Run CI/CD.
        expectation: Any corresponding expected errors for each set of parameters.
    """
    with expectation:
        validate_schedule(schedule_pattern=sch_pattern, use_ci=use_ci)


@pytest.mark.parametrize(
    'params, expected_output',
    [
        ([{'name': 'param1', 'type': int}], [{'name': 'param1', 'type': 'Integer'}]),
        ([{'name': 'param2', 'type': str}], [{'name': 'param2', 'type': 'String'}]),
        ([{'name': 'param3', 'type': float}], [{'name': 'param3', 'type': 'Float'}]),
        ([{'name': 'param4', 'type': bool}], [{'name': 'param4', 'type': 'Bool'}]),
        ([{'name': 'param5', 'type': list}], [{'name': 'param5', 'type': 'JsonArray'}]),
        ([{'name': 'param6', 'type': dict}], [{'name': 'param6', 'type': 'JsonObject'}]),
        ([{'name': 'param6', 'type': pd.DataFrame}], None)
    ]
)
def test_update_params(params: List[dict], expected_output: List[dict]):
    """Tests the update_params function, which reformats the source code type
    labels as strings. There are seven test cases for this function, which test
    for updating different parameter types.

    Args:
        params (List[dict]): Pipeline parameters. A list of dictionaries, each param is a dict containing keys:
            'name': required, str param name.
            'type': required, python primitive type.
            'description': optional, str param desc.
        expected_output (List[dict]): Expectation of whether or not the configuration is valid.
    """
    if expected_output is not None:
        assert expected_output == update_params(params=params)
    else:
        with pytest.raises(ValueError):
            assert update_params(params=params)


@pytest.mark.parametrize(
    'func, expected_output',
    [
        (func1, 'def func1(x):\n    return x + 1\n'),
        (func2, 'def func2(x, y):\n    return x + y\n'),
        (func3, 'def func3(x, y, z):\n    return x + y + z\n'),
        (func4, 'def func4():\n\n    def inner_func():\n        res = 1 + 1\n        return res\n\n    return inner_func()\n')
    ]
)
def test_get_function_source_definition(func: Callable, expected_output: str):
    """Tests get_function_source_definition, which returns a formatted string of
    the source code.

    Args:
        func (Callable): Function to pull source definition from.
        expected_output (str): Expected source definition of the given function.
    """
    assert expected_output == get_function_source_definition(func=func)


@pytest.mark.parametrize(
    'job_spec_list, expected_output',
    [
        ([{'component_spec': 'train_model',
           'display_name': 'train-model-accelerated',
           'machine_type': 'a2-highgpu-1g',
           'accelerator_type': 'NVIDIA_TESLA_A100',
           'accelerator_count': 1}],
          [{'component_spec': 'train_model',
            'spec_string':
            '''{\n'''
            '''        "accelerator_count": 1,\n'''
            '''        "accelerator_type": "NVIDIA_TESLA_A100",\n'''
            '''        "component_spec": train_model,\n'''
            '''        "display_name": "train-model-accelerated",\n'''
            '''        "machine_type": "a2-highgpu-1g"\n    }'''
         }]),
    ]
)
def test_stringify_job_spec_list(job_spec_list: List[dict], expected_output: List[dict]):
    """Tests the stringify_job_spec_list function, takes in a list of custom training job spec
    dictionaries and turns them into strings.

    Args:
        job_spec: Dictionary with job spec info. e.g.
            input = [{
                       'component_spec': 'train_model',
                       'display_name': 'train-model-accelerated',
                       'machine_type': 'a2-highgpu-1g',
                       'accelerator_type': 'NVIDIA_TESLA_A100',
                       'accelerator_count': 1
            }]
        expected_output (List[dict]): Dictionary with key value pair for component_spec,
            and a string representation of the full dictionary e.g.
            output = [{
                       'component_spec': 'train_model',
                       'spec_string': '''{
        "accelerator_count": 1,
        "accelerator_type": "NVIDIA_TESLA_A100",
        "component_spec": train_model,
        "display_name": "train-model-accelerated",
        "machine_type": "a2-highgpu-1g"
    }'''
            }]
    """

    formatted_spec = stringify_job_spec_list(job_spec_list=job_spec_list)
    assert formatted_spec == expected_output
