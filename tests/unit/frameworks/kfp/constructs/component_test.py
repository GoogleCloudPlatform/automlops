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

from mock import patch
import mock
import pytest
import os
import AutoMLOps.utils.constants
from AutoMLOps.utils.utils import read_yaml_file
from AutoMLOps.frameworks.kfp.constructs.component import KfpComponent
from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    NEWLINE,
    LEFT_BRACKET,
    RIGHT_BRACKET,
    GENERATED_COMPONENT_BASE,
    CACHE_DIR,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_JOB_SPEC_PATH,
)

#read in test data for component_spec
test_component_spec_data = read_yaml_file("tests/unit/test_data/component.yaml")

@pytest.mark.parametrize(
    """component_spec, defaults_file""",
    [
        (
    test_component_spec_data,
    "tests/unit/test_data/defaults.yaml",
        )
    ],
)

def test_init(mocker, component_spec, defaults_file):
    """Tests the initialization of the KFPPipeline class."""

    #patch global directory variables
    mocker.patch.object(AutoMLOps.utils.utils, 'CACHE_DIR', '.')

    # Create pipeline object
    component = KfpComponent(
        component_spec=component_spec,
        defaults_file=defaults_file
    )

    # Assert object properties were created properly
    assert component.task == (
        '''# Licensed under the Apache License, Version 2.0 (the "License");\n'''
        '''# you may not use this file except in compliance with the License.\n'''
        '''# You may obtain a copy of the License at\n'''
        '''#\n'''
        '''#     http://www.apache.org/licenses/LICENSE-2.0\n'''
        '''#\n'''
        '''# Unless required by applicable law or agreed to in writing, software\n'''
        '''# distributed under the License is distributed on an "AS IS" BASIS,\n'''
        '''# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n'''
        '''# See the License for the specific language governing permissions and\n'''
        '''# limitations under the License.\n'''
        '''#\n'''
        '''# DISCLAIMER: This code is generated as part of the AutoMLOps output.\n'''
        '''\n'''
        '''import argparse\n'''
        '''import json\n'''
        '''from kfp.v2.components import executor\n'''
        '''/pipelines/component/src/create_dataset.py\n'''
        '''def main():\n'''
        '''    """Main executor."""\n'''
        '''    parser = argparse.ArgumentParser()\n'''
        '''    parser.add_argument('--executor_input', type=str)\n'''
        '''    parser.add_argument('--function_to_execute', type=str)\n'''
        '''\n'''
        '''    args, _ = parser.parse_known_args()\n'''
        '''    executor_input = json.loads(args.executor_input)\n'''
        '''    function_to_execute = globals()[args.function_to_execute]\n'''
        '''\n'''
        '''    executor.Executor(\n'''
        '''        executor_input=executor_input,\n'''
        '''        function_to_execute=function_to_execute).execute()\n'''
        '''\n'''
        '''if __name__ == '__main__':\n'''
        '''    main()\n'''
    )

    assert component.compspec_image == (
            f'''{component._af_registry_location}-docker.pkg.dev/'''
            f'''{component._project_id}/'''
            f'''{component._af_registry_name}/'''
            f'''components/component_base:latest''')