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

DEFAULTS = {
    'gcp': 
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }

@pytest.fixture()
def defaults_file(tmpdir):
    """Writes temporary yaml file fixture using DEFAULTS dictionary during pytest session scope.

    Yields:
        str: Path of yaml file
    """
    yaml_path = tmpdir.join("test.yaml")
    write_yaml_file(yaml_path, DEFAULTS, 'w')
    yield yaml_path
    os.remove(yaml_path)

def test_Component(defaults_file):
    """Tests the Component base class."""

    # Set component spec to arbitrary string
    component_spec = 'Test'

    # Instantiate component base object
    my_component = Component(component_spec, defaults_file)

    # Confirm all attributes were correctly pulled from the defaults file
    assert my_component._af_registry_location == DEFAULTS['gcp']['af_registry_location']
    assert my_component._af_registry_name == DEFAULTS['gcp']['af_registry_name']
    assert my_component._project_id == DEFAULTS['gcp']['project_id']
    assert my_component._component_spec == component_spec

def test_Pipeline(defaults_file):
    """Tests the Pipeline base class"""

    # Instantiate a blank job specs
    custom_training_job_specs = [{},{}]

    # Instantiate pipeline base object
    my_pipeline = Pipeline(custom_training_job_specs, defaults_file)

    # Confirm all attributes were created as expected
    assert my_pipeline._project_id == DEFAULTS['gcp']['project_id']
    assert my_pipeline._custom_training_job_specs == custom_training_job_specs