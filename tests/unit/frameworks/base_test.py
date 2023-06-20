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

"""Unit tests for frameworks base module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from AutoMLOps.frameworks.base import Component, Pipeline
from AutoMLOps.utils.utils import write_yaml_file
import pytest
import os

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

@pytest.fixture(params=[DEFAULTS1, DEFAULTS2])
def defaults_dict(request, tmpdir):
    """Writes temporary yaml file fixture using defaults parameterized dictionaries during pytest session scope.

    Returns:
        str: Path of yaml file.
    """
    yaml_path = tmpdir.join('test.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}

@pytest.mark.parametrize(
    'component_spec',
    ['test1', 'test2']
)
def test_Component(defaults_dict, component_spec):
    """Tests the Component base class."""
    # Extract path and contents from defaults dict to create Component
    path = defaults_dict['path']
    defaults = defaults_dict['vals']

    # Instantiate component base object
    my_component = Component(component_spec=component_spec, defaults_file=path)

    # Confirm all attributes were correctly assigned
    assert my_component._af_registry_location == defaults['gcp']['af_registry_location']
    assert my_component._af_registry_name == defaults['gcp']['af_registry_name']
    assert my_component._project_id == defaults['gcp']['project_id']
    assert my_component._component_spec == component_spec

@pytest.mark.parametrize(
    'custom_training_job_specs',
    [
        [
            {},
            {}
        ],
        [
            {},
            {}
        ]
    ]
)
def test_Pipeline(defaults_dict, custom_training_job_specs):
    """Tests the Pipeline base class."""
    # Extract path and contents from defaults dict to create Component
    path = defaults_dict['path']
    defaults = defaults_dict['vals']

    # Instantiate pipeline base object
    my_pipeline = Pipeline(custom_training_job_specs=custom_training_job_specs, defaults_file=path)

    # Confirm all attributes were created as expected
    assert my_pipeline._project_id == defaults['gcp']['project_id']
    assert my_pipeline._custom_training_job_specs == custom_training_job_specs