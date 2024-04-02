# Copyright 2024 Google LLC. All Rights Reserved.
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
from typing import Callable, List, NamedTuple
from typing import Optional

import pytest

from google_cloud_automlops.orchestration.kfp.scaffold import (
    create_component_scaffold,
    create_pipeline_scaffold,
    get_packages_to_install_command,
    get_compile_step,
    get_function_parameters,
    get_pipeline_decorator,
    get_function_return_types,
)
from google_cloud_automlops.utils.constants import DEFAULT_PIPELINE_NAME
import google_cloud_automlops.utils.utils
from google_cloud_automlops.utils.utils import get_function_source_definition, read_yaml_file


def add(a: int, b: int) -> NamedTuple('output', [('sum', int)]):
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
    'func, packages_to_install, expectation, has_return_type',
    [
        (add, None, does_not_raise(), True),
        (add, ['pandas', 'pytest'], does_not_raise(), True),
        (sub, None, pytest.raises(TypeError), False)
    ]
)
def test_create_component_scaffold(func: Callable, packages_to_install: list, expectation, has_return_type: bool):
    """Tests create_component_scaffold, which creates a tmp component scaffold
    which will be used by the formalize function. Code is temporarily stored in
    component_spec['implementation']['container']['command'].

    Args:
        func (Callable): The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install (list): A list of optional packages to install before
            executing func. These will always be installed at component runtime.
        expectation: Any corresponding expected errors for each
            set of parameters.
        has_return_type: boolean indicating if the function has a return type hint.
            This is used to determine if an 'outputs' key should exist in the component scaffold.
    """
    with expectation:
        create_component_scaffold(func=func,
                                  packages_to_install=packages_to_install)

        # Assert the yaml exists
        func_path = f'.AutoMLOps-cache/{func.__name__}.yaml'
        assert os.path.exists(func_path)

        # Assert yaml contains correct keys
        component_spec = read_yaml_file(func_path)
        outputs_key = ['outputs'] if has_return_type else []
        assert set(component_spec.keys()) == set(['name', 'description', 'inputs', 'implementation', *outputs_key])
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
def test_get_packages_to_install_command(func: Callable, packages_to_install: list):
    """Tests get_packages_to_install_command, which returns a list of 
    formatted list of commands, including code for tmp storage.

    Args:
        func (Callable): The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        packages_to_install (list): A list of optional packages to install before
            executing func. These will always be installed at component runtime.
    """
    newline = '\n'
    if not packages_to_install:
        packages_to_install = []
    install_python_packages_script = (
        f'''if ! [ -x "$(command -v pip)" ]; then\n'''
        f'''    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip\n'''
        f'''fi\n'''
        f'''PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \{newline}'''
        f'''    --no-warn-script-location {' '.join([repr(str(package)) for package in packages_to_install])} && "$0" "$@"\n'''
        f'''\n''')
    assert get_packages_to_install_command(func, packages_to_install) == ['sh', '-c', install_python_packages_script, get_function_source_definition(func=func)]


@pytest.mark.parametrize(
    'func, params, expectation',
    [
        (
            add,
            [
                {'description': 'Integer a', 'name': 'a', 'type': 'Integer'},
                {'description': 'Integer b', 'name': 'b', 'type': 'Integer'}
            ],
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
def test_get_function_parameters(func: Callable, params: List[dict], expectation):
    """Tests get_function_parameters, which returns a formatted list of
    parameters.

    Args:
        func (Callable): The python function to create a component from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        params (List[dict]): Params list with types converted to kubeflow spec.
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
def test_create_pipeline_scaffold(mocker, func: Callable, name: str, description: str):
    """Tests create_pipeline_scaffold, which creates a temporary pipeline 
    scaffold which will be used by the formalize function.

    Args:
        mocker: Mocker used to patch constants to test in tempoarary
            environment.
        func (Callable): The python function to create a pipeline from. The 
            function should have type annotations for all its arguments,
            indicating how it is intended to be used (e.g. as an input/output
            Artifact object, a plain parameter, or a path to a file).
        name (str): The name of the pipeline.
        description (str): Short description of what the pipeline does.
    """
    mocker.patch.object(google_cloud_automlops.utils.utils, 'CACHE_DIR', '.')
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
def test_get_pipeline_decorator(name: str, description: str):
    """Tests get_pipeline_decorator, which creates the kfp pipeline decorator.

    Args:
        name (str): The name of the pipeline.
        description (str): Short description of what the pipeline does.
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
def test_get_compile_step(func_name: str):
    """Tests get_compile_step, which creates the compile function call.

    Args:
        func_name (str): The name of the pipeline function.
    """
    assert get_compile_step(func_name=func_name) == (
        f'\n'
        f'compiler.Compiler().compile(\n'
        f'    pipeline_func={func_name},\n'
        f'    package_path=pipeline_job_spec_path)\n'
        f'\n'
    )


@pytest.mark.parametrize(
    'return_annotation, return_types, expectation',
    [
        (
            NamedTuple('output', [('sum', int)]),
            [{'description': None, 'name': 'sum', 'type': 'Integer'},],
            does_not_raise()
        ),
        (
            NamedTuple('output', [('first', str), ('last', str)]),
            [{'description': None, 'name': 'first', 'type': 'String'},
             {'description': None, 'name': 'last', 'type': 'String'},],
            does_not_raise()
        ),
        (
            Optional[NamedTuple('output', [('count', int)])],
            None,
            pytest.raises(TypeError)
        ),
        (
            int,
            None,
            pytest.raises(TypeError)
        ),(
            None,
            None,
            pytest.raises(TypeError)
        ),
        (
            'NO_ANNOTATION',
            None,
            does_not_raise()
        )
    ]
)
def test_get_function_return_types(return_annotation, return_types: List[dict], expectation):
    """Tests get_function_outputs, which returns a formatted list of
    return types.

    Args:
        annotation (Any): The return type to test.
        return_types (List[dict]): The return type converted into the kubeflow output spec.
        expectation: Any corresponding expected errors for each
            set of parameters.
    """

    def func():
        ...

    if return_annotation != 'NO_ANNOTATION':
        func.__annotations__ = {'return' : return_annotation}

    with expectation:
        assert return_types == get_function_return_types(func=func)
