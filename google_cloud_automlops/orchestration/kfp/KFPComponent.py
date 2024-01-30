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

"""Creates a KFP component object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Callable, List, Optional
from google_cloud_automlops.orchestration.Component import Component

from google_cloud_automlops.utils.constants import (
    PLACEHOLDER_IMAGE,
    CACHE_DIR
)
from google_cloud_automlops.utils.utils import (
    make_dirs,
    write_yaml_file
)


class KFPComponent(Component):
    def __init__(self, 
                 func: Optional[Callable] = None, 
                 packages_to_install: Optional[List[str]] = None):
        """Initiates a KFP component object created out of a function holding
        all necessary code.

        Args:
            func: The python function to create a component from. The function
                should have type annotations for all its arguments, indicating how
                it is intended to be used (e.g. as an input/output Artifact object,
                a plain parameter, or a path to a file).
            packages_to_install: A list of optional packages to install before
                executing func. These will always be installed at component runtime.
        """
        super().__init__(func, packages_to_install)
        self.parameters = update_params(self.parameters)
        self.return_types = update_params(self.return_types)
        self.packages_to_install_command = self._get_packages_to_install_command()
        self.component_spec = self._create_component_spec()

    def build(self):
        """Constructs files for running and managing Kubeflow pipelines.
        """
        # Write component yaml
        filename = CACHE_DIR + f'/{self.name}.yaml'
        make_dirs([CACHE_DIR])
        write_yaml_file(filename, self.component_spec, 'w')

    def _get_packages_to_install_command(self):
        """Returns a list of formatted list of commands, including code for tmp storage.
        """
        newline = '\n'
        concat_package_list = ' '.join([repr(str(package)) for package in self.packages_to_install])
        install_python_packages_script = (
            f'''if ! [ -x "$(command -v pip)" ]; then{newline}'''
            f'''    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip{newline}'''
            f'''fi{newline}'''
            f'''PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \{newline}'''
            f'''    --no-warn-script-location {concat_package_list} && "$0" "$@"{newline}'''
            f'''{newline}''')
        return ['sh', '-c', install_python_packages_script, self.src_code]

    def _create_component_spec(self):
        """Creates a tmp component scaffold which will be used by the formalize function.
        Code is temporarily stored in component_spec['implementation']['container']['command'].

        Returns:
            _type_: _description_ #TODO: FILL OUT
        """
        # Instantiate component yaml attributes
        component_spec = {}
        component_spec['name'] = self.name
        if self.description:
            component_spec['description'] = self.description
        outputs = self.return_types
        if outputs:
            component_spec['outputs'] = outputs
        component_spec['inputs'] = self.parameters
        component_spec['implementation'] = {}
        component_spec['implementation']['container'] = {}
        component_spec['implementation']['container']['image'] = PLACEHOLDER_IMAGE
        component_spec['implementation']['container']['command'] = self.packages_to_install_command
        component_spec['implementation']['container']['args'] = ['--executor_input',
                                                                {'executorInput': None},
                                                                '--function_to_execute', 
                                                                self.name]
        return component_spec

def update_params(params: list) -> list:
    """Converts the parameter types from Python types
    to Kubeflow types. Currently only supports
    Python primitive types.

    Args:
        params: Pipeline parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
    Returns:
        list: Params list with converted types.
    Raises:
        Exception: If an inputted type is not a primitive.
    """
    python_kfp_types_mapper = {
        int: 'Integer',
        str: 'String',
        float: 'Float',
        bool: 'Bool',
        list: 'JsonArray',
        dict: 'JsonObject'
    }
    for param in params:
        try:
            param['type'] = python_kfp_types_mapper[param['type']]
        except KeyError as err:
            raise ValueError(f'Unsupported python type - we only support '
                            f'primitive types at this time. {err}') from err
    return params
