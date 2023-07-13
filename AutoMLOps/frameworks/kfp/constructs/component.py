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

"""Code strings for a kfp component."""

# pylint: disable=line-too-long

from AutoMLOps.utils.constants import GENERATED_LICENSE
from AutoMLOps.utils.utils import is_using_kfp_spec
from AutoMLOps.frameworks.base import Component

class KfpComponent(Component):
    """Child class that generates files related to kfp components."""
    def __init__(self, component_spec: dict, defaults_file: str):
        """Instantiate Component scripts object with all necessary attributes.

        Args:
            component_spec (dict): Dictionary of component specs including details
                of component image, startup command, and args.
            defaults_file (str): Path to the default config variables yaml.
        """
        super().__init__(component_spec, defaults_file)

        # Get generated scripts as public attributes
        self.task = self._create_task()
        self.compspec_image = self._create_compspec_image()

    def _create_task(self):
        """Creates the content of the cell python code to be written to a file with required imports.

        Returns:
            str: Contents of component base source code.
        """
        default_imports = (GENERATED_LICENSE +
            'import argparse\n'
            'import json\n'
            'from kfp.v2.components import executor\n')
        if not is_using_kfp_spec(self._component_spec['implementation']['container']['image']):
            custom_imports = ('\n'
            'import kfp\n'
            'from kfp.v2 import dsl\n'
            'from kfp.v2.dsl import *\n'
            'from typing import *\n'
            '\n')
        else:
            custom_imports = '' # the above is already included as part of the kfp spec
        custom_code = self._component_spec['implementation']['container']['command'][-1]
        main_func = (
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
            '''    main()\n''')
        return default_imports + custom_imports + custom_code + main_func

    def _create_compspec_image(self):
        """Write the correct image for the component spec.

        Returns:
            str: Component spec image.
        """
        return (
            f'''{self._af_registry_location}-docker.pkg.dev/'''
            f'''{self._project_id}/'''
            f'''{self._af_registry_name}/'''
            f'''components/component_base:latest''')
