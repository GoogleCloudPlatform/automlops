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

"""Unit tests for component constructs kfp module."""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access

import pytest

from AutoMLOps.frameworks.kfp.constructs.component import KfpComponent
from AutoMLOps.utils.constants import GENERATED_LICENSE
from AutoMLOps.utils.utils import is_using_kfp_spec, write_yaml_file

# Create defaults file contents to test
DEFAULTS1 = {
    'gcp': 
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }
DEFAULTS2 = {
    'gcp': 
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }

# Create component specs to test
COMPONENT_SPEC1 = {
    'implementation':
        {
            'container': 
                {
                    'command': 'echo hi',
                    'image': 'hi'
                }
        }
}
COMPONENT_SPEC2 = {
    'implementation':
        {
            'container': 
                {
                    'command': 'echo hi',
                    'image': 'AutoMLOps_image_tbd'
                }
        }
}

@pytest.fixture(name='defaults_dict', params=[DEFAULTS1, DEFAULTS2])
def fixture_defaults_dict(request: pytest.FixtureRequest, tmpdir: pytest.FixtureRequest):
    """Writes temporary yaml file fixture using defaults parameterized
    dictionaries during pytest session scope.

    Args:
        request: Pytest fixture special object that provides information
            about the fixture.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.

    Returns:
        dict: Path of yaml file and dictionary it contains
    """
    yaml_path = tmpdir.join('test.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}

@pytest.mark.parametrize(
    'component_spec',
    [COMPONENT_SPEC1, COMPONENT_SPEC2]
)
def test_KfpComponent(component_spec: dict, defaults_dict: pytest.FixtureRequest):
    """Tests the KFP child class that generates files related to KFP components.

    Args:
        component_spec (dict): Dictionary of component specs including details
            of component image, startup command, and args.
        defaults_dict (dict): Dictionary containing the path to the default config
            variables yaml and the dictionary held within it.
    """
    # Extract path and contents from defaults dict to create KFP Component
    path = defaults_dict['path']
    defaults = defaults_dict['vals']
    comp = KfpComponent(component_spec=component_spec, defaults_file=path)

    # Confirm attributes were correctly assigned
    assert comp._af_registry_location == defaults['gcp']['af_registry_location']
    assert comp._af_registry_name == defaults['gcp']['af_registry_name']
    assert comp._project_id == defaults['gcp']['project_id']
    assert comp._component_spec == component_spec

    # Confirm generated scripts were correctly created
    opt1 = ('\n'
            'import kfp\n'
            'from kfp.v2 import dsl\n'
            'from kfp.v2.dsl import *\n'
            'from typing import *\n'
            '\n')
    opt2 = ''
    assert comp.task == (
        GENERATED_LICENSE +
        f'''import argparse\n'''
        f'''import json\n'''
        f'''from kfp.v2.components import executor\n'''
        f'''{opt1 if not is_using_kfp_spec(component_spec["implementation"]["container"]["image"]) else opt2}'''
        f'''{component_spec["implementation"]["container"]["command"][-1]}'''
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
        '''    main()\n'''
    )

    assert comp.compspec_image == (
            f'''{defaults['gcp']['af_registry_location']}-docker.pkg.dev/'''
            f'''{defaults['gcp']['project_id']}/'''
            f'''{defaults['gcp']['af_registry_name']}/'''
            f'''components/component_base:latest''')
