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

import os

from AutoMLOps.utils.utils import (
    write_yaml_file
)

from AutoMLOps.frameworks.base import (
    Component,
    Pipeline
)

DEFAULTS = {
    'gcp': 
        {
            'af_registry_location': 'us-central1',
            'project_id': 'my_project',
            'af_registry_name': 'my_af_registry'
        }
    }

def test_Component():
    """Tests the Component base class."""
    component_spec = "Test."
    write_yaml_file('test.yaml', DEFAULTS, 'w')
    my_component = Component(component_spec, 'test.yaml')
    assert my_component._af_registry_location == DEFAULTS['gcp']['af_registry_location']
    assert my_component._af_registry_name == DEFAULTS['gcp']['af_registry_name']
    assert my_component._project_id == DEFAULTS['gcp']['project_id']
    assert my_component._component_spec == component_spec
    os.remove('test.yaml')
    
def test_Pipeline():
    """Tests the Pipeline base class"""
    custom_training_job_specs = [{},{}]
    write_yaml_file('test.yaml', DEFAULTS, 'w')
    my_pipeline = Pipeline(custom_training_job_specs, 'test.yaml')
    assert my_pipeline._project_id == DEFAULTS['gcp']['project_id']
    assert my_pipeline._custom_training_job_specs == custom_training_job_specs
    os.remove('test.yaml')