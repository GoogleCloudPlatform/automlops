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
import pandas as pd
import pytest
import yaml
from contextlib import nullcontext as does_not_raise

import AutoMLOps.utils.utils
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

@pytest.mark.parametrize(
    "directories, existance, expectation",
    [
        (["dir1", "dir2"], [True, True], does_not_raise()),
        (["dir1", "dir1"], [True, False], does_not_raise()),
        (["\0", "dir1"], [True, True], pytest.raises(ValueError))
    ]
)
def test_make_dirs(directories, existance, expectation):
    """Tests make_dirs, which creates a list of directories if they do 
    not already exist. There are three test cases for this function:
        1. Expected outcome, folders created as expected.
        2. Duplicate folder names given, expecting only one folder created.
        3. Invalid folder name given, expects an error.

    Args:
        directories: List of directories to be created.
        existance: List of booleans indicating whether the
            listed directories to be created are expected to
            exist after invoking make_dirs.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    with expectation:
        make_dirs(directories=directories)
        for dir, exist in zip(directories, existance):
            assert os.path.exists(dir) == exist
            if exist:
                os.rmdir(dir)

@pytest.mark.parametrize(
    "filepath, content1, content2, expectation",
    [
        ("test.yaml", {"key1": "value1", "key2": "value2"}, None, does_not_raise()),
        ("test.yaml", {"key1": "value1", False: "random stuff"}, r"-A fails", pytest.raises(yaml.YAMLError))
    ]
)
def test_read_yaml_file(filepath, content1, content2, expectation):
    """Tests read_yaml_file, which reads a yaml file and returns the file
    contents as a dict. There are two sets of test cases for this function:
        1. Expected outcome, file read in with correct content.
        2. File to be read is not in standard yaml format, expects a yaml error.

    Args:
        filepath: Path to yaml file to be read.
        content1: First set of content to be included in the yaml
            at the given file path.
        content2: Second set of content to be included in the yaml
            at the given file path.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    with open(file=filepath, mode="w", encoding="utf-8") as file:
        if content1:
            yaml.dump(content1, file)
        if content2:
            yaml.dump(content2, file)
    with expectation:
        assert read_yaml_file(filepath=filepath) == content1
    os.remove(path=filepath)

@pytest.mark.parametrize(
    "filepath, mode, expectation",
    [
        ("test.yaml", "w", does_not_raise()),
        ("/nonexistent/directory", "w",  pytest.raises(FileNotFoundError)),
        ("test.yaml", "r", pytest.raises(IOError))
    ]
)
def test_write_yaml(filepath, mode, expectation):
    """Tests write_yaml_file, which writes a yaml file. There are three
    sets of test cases for this function:
            1. Expected outcome, yaml is written correctly.
            2. Invalid file path given, expecting a FileNotFoundError.
            3. Invalid mode given, expecting an IOError.

    Args:
        filepath: Path for yaml file to be written.
        mode: Read/write mode to be used.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    contents = {"key1": "value1", "key2": "value2"}
    with expectation:
        write_yaml_file(
            filepath=filepath,
            contents=contents,
            mode=mode
        )
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            yaml.safe_load(filepath) == contents
        os.remove(path=filepath)

@pytest.mark.parametrize(
    "filepath, text, write_file, expectation",
    [
        ("test.txt", "This is a text file.", True, does_not_raise()),
        ("fail", "", False, pytest.raises(FileNotFoundError))
    ]
)
def test_read_file(filepath, text, write_file, expectation):
    """Tests read_file, which reads a text file in as a string. There
    are two sets of test cases for this function:
        1. Expected outcome, file is read correctly.
        2. Invalid file path given (file was not written), expecting
            a FileNotFoundError.

    Args:
        filepath: Path for file to be read from.
        text: Text expected to be read from the given file.
        write_file: Whether or not the file should be written for this
            test case.
        expectation: Any corresponding expected errors for each set
            of parameters.
    """
    if write_file:
        with open(file=filepath, mode="w", encoding="utf-8") as file:
            file.write(text)
    with expectation:
        assert read_file(filepath=filepath) == text
    if os.path.exists(filepath):
        os.remove(filepath)

@pytest.mark.parametrize(
    "filepath, text, mode, expectation",
    [
        ("test.txt", "This is a test file.", "w", does_not_raise()),
        (15, "This is a test file.", "w", pytest.raises(OSError))
    ]
)
def test_write_file(filepath, text, mode, expectation):
    """Tests write_file, which writes a string to a text file. There
    are two test cases for this function:
        1. Expected outcome, file is written as expected.
        2. Invalid file path given (file was not written), expecting
            an OSError.

    Args:
        filepath: Path for file to be written.
        text: Content to be written to the file at the given filepath.
        mode: Read/write mode to be used.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    with expectation:
        write_file(
            filepath=filepath,
            text=text,
            mode=mode
        )
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as file:
            assert text == file.read()
        os.remove(filepath)

def test_write_and_chmod():
    """Tests write_and_chmod, which writes a file at the specified path
    and chmods the file to allow for execution.
    """
    # Create a file.
    with open("test.txt", "w", encoding="utf-8") as file:
        file.write("This is a test file.")

    # Call the `write_and_chmod` function.
    write_and_chmod("test.txt", "This is a test file.")

    # Assert that the file exists and is executable.
    assert os.path.exists("test.txt")
    assert os.access("test.txt", os.X_OK)

    # Assert that the contents of the file are correct.
    with open("test.txt", "r", encoding="utf-8") as file:
        contents = file.read()
    assert contents == "This is a test file."
    os.remove("test.txt")

def test_delete_file():
    """Tests delete_file, which deletes a file at the specified path."""
    with open("test.txt", "w", encoding="utf-8") as file:
        file.write("This is a test file.")
    delete_file("test.txt")
    assert not os.path.exists("test.txt")

@pytest.mark.parametrize(
    "comp_path, comp_name, patch_cwd, expectation",
    [
        (["component.yaml"], ["component"], True, does_not_raise()),
        ([], [], True, does_not_raise()),
        (["component.yaml"], ["component"], False, pytest.raises(FileNotFoundError))
    ]
)
def test_get_components_list(mocker, comp_path, comp_name, patch_cwd, expectation):
    """Tests get_components_list, which reads yamls in tmpfiles directory,
    verifies they are component yamls, and returns the name of the files.
    There are three test cases for this function:
        1. Expected outcome, component list is pulled as expected.
        2. Verifies an empty list comes back if no YAMLs are present.
        3. Call function with a nonexistent dir, expecting OSError.

    Args:
        mocker: Mocker to patch the cache directory for component files.
        comp_path: Path(s) to component yamls.
        comp_name: Name(s) of components.
        patch_cwd: Boolean flag indicating whether to patch the current working directory from CACHE_DIR to root
        expectation: Any corresponding expected errors for each set of parameters.
    """
    if patch_cwd:
        mocker.patch.object(AutoMLOps.utils.utils, "CACHE_DIR", ".")
    if comp_path:
        for file in comp_path:
            with open(file, "w") as f:
                yaml.dump({"name": "value1", "inputs": "value2", "implementation": "value3"}, f)
    with expectation:
        assert get_components_list(full_path=False) == comp_name
        assert get_components_list(full_path=True) == [os.path.join(".", file) for file in comp_path]
    for file in comp_path:
        if os.path.exists(file):
            os.remove(file)

@pytest.mark.parametrize(
    "yaml_contents, expected",
    [
        (
            {
                "name": "value1",
                "inputs": "value2",
                "implementation": "value3"
            },
            True
        ),
        (
            {
                "name": "value1",
                "inputs": "value2"
            },
            False
        )
    ]
)
def test_is_component_config(yaml_contents, expected):
    """Tests is_component_config, which which checks to see if the given
    file is a component yaml. There are two test cases for this function:
        1. A valid component is given, expecting return value True.
        2. An invalid component is given, expecting return value False.

    Args:
        yaml_contents: Component configurations to be written to yaml file.
        expected: Expectation of whether or not the configuration is valid.
    """
    with open("component.yaml", "w") as f:
        yaml.dump(yaml_contents, f)
    assert expected == is_component_config("component.yaml")
    os.remove("component.yaml")

@pytest.mark.parametrize(
    "command, expectation",
    [
        ("touch test.txt", False),
        ("not a real command", True)
    ]
)
def test_execute_process(command, expectation):
    """Tests execute_process, which executes an external shell process. There are two
    test cases for this function:
        1. A valid command to create a file, which is expected to run successfully.
        2. An invalid command, which is expected to raise a RunTime Error.

    Args:
        command: Command that is to be executed.
        raises_error: Whether or not an error is expected to be raised.
    """
    if expectation:
        with pytest.raises(RuntimeError):
            execute_process(command=command, to_null=False)
    else:
        execute_process(command=command, to_null=False)
        assert os.path.exists("test.txt")
        os.remove("test.txt")

@pytest.mark.parametrize(
    "sch_pattern, run_local, expectation",
    [
        ("No Schedule Specified", True, does_not_raise()),
        ("No Schedule Specified", False, does_not_raise()),
        ("Schedule", True, pytest.raises(ValueError)),
        ("Schedule", False, does_not_raise())
    ]
)
def test_validate_schedule(sch_pattern, run_local, expectation):
    """Tests validate_schedule, which validates the inputted schedule
    parameter. There are four test cases for this function, which tests each
    combination of sch_pattern and run_loc for the expected results.

    Args:
        sch_pattern: Cron formatted value used to create a Scheduled retrain job.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
        expectation: Any corresponding expected errors for each set of parameters.
    """
    with expectation:
        validate_schedule(schedule_pattern=sch_pattern, run_local=run_local)

@pytest.mark.parametrize(
    "params, expected",
    [
        ([{"name": "param1", "type": int}], [{"name": "param1", "type": "Integer"}]),
        ([{"name": "param2", "type": str}], [{"name": "param2", "type": "String"}]),
        ([{"name": "param3", "type": float}], [{"name": "param3", "type": "Float"}]),
        ([{"name": "param4", "type": bool}], [{"name": "param4", "type": "Bool"}]),
        ([{"name": "param5", "type": list}], [{"name": "param5", "type": "List"}]),
        ([{"name": "param6", "type": dict}], [{"name": "param6", "type": "Dict"}]),
        ([{"name": "param6", "type": pd.DataFrame}], None)
    ]
)
def test_update_params(params, expected):
    """Tests the update_params function, which reformats the source code type
    labels as strings. There are seven test cases for this function, which test
    for updating different parameter types.

    Args:
        params: Pipeline parameters. A list of dictionaries, each param is a dict containing keys:
            'name': required, str param name.
            'type': required, python primitive type.
            'description': optional, str param desc.
        expected: Expectation of whether or not the configuration is valid.
    """
    if expected is not None:
        assert expected == update_params(params=params)
    else:
        with pytest.raises(ValueError):
            assert update_params(params=params)

def func1(x):
    return x + 1
def func2(x, y):
    return x + y
def func3(x, y, z):
    return x + y + z
def func4():
    def inner_func():
        res = 1 + 1
    return inner_func()

@pytest.mark.parametrize(
    "func, expected",
    [
        (func1, "def func1(x):\n    return x + 1\n"),
        (func2, "def func2(x, y):\n    return x + y\n"),
        (func3, "def func3(x, y, z):\n    return x + y + z\n"),
        (func4, "def func4():\n    def inner_func():\n        res = 1 + 1\n    return inner_func()\n")
    ]
)
def test_get_function_source_definition(func, expected):
    """Tests get_function_source_definition, which returns a formatted string of the source code.

    Args:
        func: Function to pull source definition from.
        expected: Expected source definition of the given function.
    """
    assert expected == get_function_source_definition(func=func)

@pytest.mark.parametrize(
    "job_spec, expected",
    [
        ({"component_spec": "train_model"}, "{\n       'component_spec': train_model,\n    }\n"),
        ({"component_spec": "train_model", "other_spec": "other_value"}, "{\n       'component_spec': train_model,\n       'other_spec': 'other_value',\n    }\n"),
        ({}, "{\n    \n    }\n"),
        ({"{": "}"},"{\n       '{': '}',\n    }\n" )
    ]
)
def test_format_spec_dict(job_spec, expected):
    """Tests format_spec_dict, which takes in a spec dictionary and
    removes the quotes around the component op name.

    Args:
        job_spec: Component spec dictionary.
        expected: Expected outcome.
    """
    formatted_spec = format_spec_dict(job_spec=job_spec)
    assert formatted_spec == expected
