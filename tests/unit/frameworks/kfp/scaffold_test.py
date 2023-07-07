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

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from contextlib import nullcontext as does_not_raise
import os
import pytest
from AutoMLOps.frameworks.kfp.scaffold import (
    create_component_scaffold,
    create_pipeline_scaffold,
    get_packages_to_install_command,
    get_compile_step,
    get_function_parameters,
    get_pipeline_decorator,
)
import AutoMLOps.utils.utils
from AutoMLOps.utils.utils import get_function_source_definition, read_yaml_file
from AutoMLOps.utils.constants import DEFAULT_PIPELINE_NAME

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

def div(a: float, b: float):
    """Testing

    Args:
        a (float): Float a
        b (float): Float b
    """
    return a/b

@pytest.mark.parametrize(
    'func, packages_to_install, expectation',
    [
        (add, None, does_not_raise()),
        (add, ['pandas', 'pytest'], does_not_raise()),
        (sub, None, pytest.raises(TypeError))
    ]
)
def test_create_component_scaffold(func, packages_to_install, expectation):
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
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    with expectation:
        create_component_scaffold(func=func,
                                  packages_to_install=packages_to_install)

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
        (add, ['pandas']),
        (sub, ['pandas', 'kfp', 'pytest'])
    ]
)
def test_get_packages_to_install_command(func, packages_to_install):
    """Tests get_packages_to_install_command, which returns a list of 
    formatted list of commands, including code for tmp storage.

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
            [
                {'description': 'Integer a', 'name': 'a', 'type': 'Integer'},
                {'description': 'Integer b', 'name': 'b', 'type': 'Integer'}],
            does_not_raise()
        ),
        (
            sub,
            None,
            pytest.raises(TypeError)
        ),
        (
            div,
            [
                {'description': 'Float a', 'name': 'a', 'type': 'Float'},
                {'description': 'Float b', 'name': 'b', 'type': 'Float'}
            ],
            does_not_raise()
        )
    ]
)
def test_get_function_parameters(func, params, expectation):
    """Tests get_function_parameters, which returns a formatted list of
    parameters.

    Args:
        func: The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        params: Params list with types converted to kubeflow spec.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """
    with expectation:
        assert params == get_function_parameters(func=func)

@pytest.mark.parametrize(
    'func, name, description',
    [
        (add, 'Add', 'This is a test'),
        (sub, 'Sub', 'Test 2'),
        (div, None, None)
    ]
)
def test_create_pipeline_scaffold(mocker, func, name, description):
    """Tests create_pipeline_scaffold, which creates a temporary pipeline 
    scaffold which will be used by the formalize function.

    Args:
        mocker: Mocker used to patch constants to test in tempoarary
            environment.
        func: The python function to create a pipeline from. The function should
            have type annotations for all its arguments, indicating how it is
            intended to be used (e.g. as an input/output Artifact object, a
            plain parameter, or a path to a file).
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
    """
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')
    create_pipeline_scaffold(func=func, name=name, description=description)
    fold = '.AutoMLOps-cache'
    file_path = 'pipeline_scaffold.py'
    assert os.path.exists(os.path.join(fold, file_path))
    os.remove(os.path.join(fold, file_path))
    os.rmdir(fold)

@pytest.mark.parametrize(
    'name, description',
    [
        ('Name1', 'Description1'),
        ('Name2', 'Description2'),
        (None, None),
    ]
)
def test_get_pipeline_decorator(name, description):
    """Tests get_pipeline_decorator, which creates the kfp pipeline decorator.

    Args:
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
    """
    desc_str = f'''    description='{description}',\n''' if description else ''
    decorator = (
        f'''@dsl.pipeline'''
        f'''(\n    name='{DEFAULT_PIPELINE_NAME if not name else name}',\n'''
        f'''{desc_str}'''
        f''')\n'''
    )
    assert decorator == get_pipeline_decorator(name=name, description=description)

@pytest.mark.parametrize(
    'func_name',
    ['func1', 'func2']
)
def test_get_compile_step(func_name):
    """Tests get_compile_step, which creates the compile function call.

    Args:
        func_name: The name of the pipeline function.
    """
    assert get_compile_step(func_name=func_name) == (
        f'\n'
        f'compiler.Compiler().compile(\n'
        f'    pipeline_func={func_name},\n'
        f'    package_path=pipeline_job_spec_path)\n'
        f'\n'
    )
