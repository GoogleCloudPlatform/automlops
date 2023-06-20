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

"""Unit tests for kfp scaffold module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from contextlib import nullcontext as does_not_raise
import mock
import os
import pytest
from AutoMLOps.frameworks.kfp.scaffold import (
    create_component_scaffold,
    get_packages_to_install_command,
    get_function_parameters,
    maybe_strip_optional_from_annotation,
    create_pipeline_scaffold
)
import AutoMLOps.utils.utils
from AutoMLOps.utils.utils import get_function_source_definition, read_yaml_file

def add(a: int, b: int):
    """Testing

    Args:
        a (int): Integer a
        b (int): Integer b

    Returns:
        int: Sum of a and b
    """
    return a + b

def sub(a, b):
    return a - b

@pytest.mark.parametrize(
    'func, packages_to_install',
    [
        (add, None),
        (add, ['pandas'])
    ]
)
def test_create_component_scaffold(mocker, func, packages_to_install):
    """Tests create_component_scaffold, which creates a tmp component scaffold
    which will be used by the formalize function. Code is temporarily stored in
    component_spec['implementation']['container']['command'].

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install: A list of optional packages to install before
            executing func. These will always be installed at component runtime.
    """
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')
    create_component_scaffold(func=func, packages_to_install=packages_to_install)

    # Assert the yaml exists
    func_path = f'.AutoMLOps-cache/{func.__name__}.yaml'
    assert os.path.exists(func_path)

    # Assert yaml contains correct keys
    component_spec = read_yaml_file(func_path)
    assert list(component_spec.keys()) == ['name', 'description', 'inputs', 'implementation']
    assert list(component_spec['implementation'].keys()) == ['container']
    assert list(component_spec['implementation']['container'].keys()) == ['image', 'command', 'args']

    # Remove temporary files
    os.remove(func_path)
    os.rmdir('.AutoMLOps-cache')

@pytest.mark.parametrize(
    'func, packages_to_install',
    [
        (add, None),
        (add, ['pandas'])
    ]
)
def test_get_packages_to_install_command(mocker, func, packages_to_install):
    newline = '\n'
    if not packages_to_install:
        packages_to_install = []
    install_python_packages_script = (
        f'''if ! [ -x "$(command -v pip)" ]; then{newline}'''
        f'''    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip{newline}'''
        f'''fi{newline}'''
        f'''PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \{newline}'''
        f'''    --no-warn-script-location {' '.join([repr(str(package)) for package in packages_to_install])} && "$0" "$@"{newline}'''
        f'''{newline}''')
    assert get_packages_to_install_command(func, packages_to_install) == ['sh', '-c', install_python_packages_script, get_function_source_definition(func=func)]

@pytest.mark.parametrize(
    'func, params, expectation',
    [
        (
            add,
            [{'description': 'Integer a', 'name': 'a', 'type': 'Integer'}, {'description': 'Integer b', 'name': 'b', 'type': 'Integer'}],
            does_not_raise()
        ),
        (
            sub,
            None,
            pytest.raises(TypeError)
        )
    ]
)
def test_get_function_parameters(func, params, expectation):
    with expectation:
        assert params == get_function_parameters(func=func)

@pytest.mark.parametrize(
    'annotation, result, expectation',
    [
        ('Optional[str]', 'str', does_not_raise())
    ]
)
def test_maybe_strip_optional_from_annotation(annotation, result, expectation):
    assert result == maybe_strip_optional_from_annotation(annotation)