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

"""Defines parent classes for a Component and Pipeline."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Dict, List
from AutoMLOps.utils.utils import read_yaml_file

class Component():
    """Parent class that defines a general abstraction of a Component."""
    def __init__(self, component_spec: dict, defaults_file: str):
        """Instantiate Component scripts object with all necessary attributes.

        Args:
            component_spec (dict): Dictionary of component specs including details
                of component image, startup command, and args.
            defaults_file (str): Path to the default config variables yaml.
        """
        self._component_spec = component_spec

        # Parse defaults file for hidden class attributes
        defaults = read_yaml_file(defaults_file)
        self._af_registry_location = defaults['gcp']['af_registry_location']
        self._project_id = defaults['gcp']['project_id']
        self._af_registry_name = defaults['gcp']['af_registry_name']

class Pipeline():
    """Parent class that defines a general abstraction of a Pipeline """
    def __init__(self, custom_training_job_specs: List[Dict], defaults_file: str):
        """Instantiate Pipeline scripts object with all necessary attributes.

        Args:
            custom_training_job_specs (List[Dict]): Specifies the specs to run the training job with.
            defaults_file (str): Path to the default config variables yaml.
        """
        self._custom_training_job_specs = custom_training_job_specs

        defaults = read_yaml_file(defaults_file)
        self._project_id = defaults['gcp']['project_id']
