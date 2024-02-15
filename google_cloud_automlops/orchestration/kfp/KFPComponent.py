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

"""Creates a KFP component subclass."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Callable, List, Optional

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.orchestration.Component import Component
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_LICENSE,
    KFP_TEMPLATES_PATH,
    PLACEHOLDER_IMAGE,
)
from google_cloud_automlops.utils.utils import (
    make_dirs,
    render_jinja,
    write_file,
    write_yaml_file
)


class KFPComponent(Component):
    """Creates a KFP specific Component object for #TODO: add more

    Args:
        Component (object): Generic Component object.
    """

    def __init__(self,
                 func: Optional[Callable] = None, 
                 packages_to_install: Optional[List[str]] = None):
        """Initiates a KFP Component object created out of a function holding
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

        # Update parameters and return types to reflect KFP data types
        if self.parameters:
            self.parameters = update_params(self.parameters)
        if self.return_types:
            self.return_types = update_params(self.return_types)

        # Set packages to install and component spec attributes
        self.packages_to_install_command = self._get_packages_to_install_command()
        self.component_spec = self._create_component_spec()

    def build(self):
        """Constructs files for running and managing Kubeflow pipelines.
        """
        super().build()

        # Set and create directory for components if it does not already exist
        component_dir = BASE_DIR + 'components/' + self.component_spec['name']

        # Build necessary folders
        # TODO: make this only happen for the first component? or pull into automlops.py
        make_dirs([
            component_dir,
            BASE_DIR + 'components/component_base/src/'])

        # TODO: can this be removed?
        kfp_spec_bool = self.component_spec['implementation']['container']['image'] != PLACEHOLDER_IMAGE

        # Read in component specs
        custom_code_contents = self.component_spec['implementation']['container']['command'][-1]
        compspec_image = (
                f'''{self.artifact_repo_location}-docker.pkg.dev/'''
                f'''{self.project_id}/'''
                f'''{self.artifact_repo_name}/'''
                f'''{self.naming_prefix}/'''
                f'''components/component_base:latest''')

        # If using kfp, remove spaces in name and convert to lowercase
        if kfp_spec_bool:
            self.component_spec['name'] = self.component_spec['name'].replace(' ', '_').lower()

        # Write task script to component base
        write_file(
            filepath=BASE_DIR + 'components/component_base/src/' + self.component_spec['name'] + '.py',
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.components.component_base.src') / 'task.py.j2',
                generated_license=GENERATED_LICENSE,
                kfp_spec_bool=kfp_spec_bool,
                custom_code_content=custom_code_contents),
            mode='w')

        # Update component_spec to include correct image and startup command
        self.component_spec['implementation']['container']['image'] = compspec_image
        self.component_spec['implementation']['container']['command'] = [
            'python3',
            f'''/pipelines/component/src/{self.component_spec['name']+'.py'}''']

        # Write license and component spec to the appropriate component.yaml file
        comp_yaml_path = component_dir + '/component.yaml'
        write_file(
            filepath=comp_yaml_path,
            text=GENERATED_LICENSE,
            mode='w')
        write_yaml_file(
            filepath=comp_yaml_path,
            contents=self.component_spec,
            mode='a')

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
