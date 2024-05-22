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

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

# WIP

'''
@pytest.mark.parametrize(
    'params, expected_output',
    [
        ([{'name': 'param1', 'type': int}], [{'name': 'param1', 'type': 'Integer'}]),
        ([{'name': 'param2', 'type': str}], [{'name': 'param2', 'type': 'String'}]),
        ([{'name': 'param3', 'type': float}], [{'name': 'param3', 'type': 'Float'}]),
        ([{'name': 'param4', 'type': bool}], [{'name': 'param4', 'type': 'Boolean'}]),
        ([{'name': 'param5', 'type': list}], [{'name': 'param5', 'type': 'JsonArray'}]),
        ([{'name': 'param6', 'type': dict}], [{'name': 'param6', 'type': 'JsonObject'}]),
        ([{'name': 'param6', 'type': pd.DataFrame}], None)
    ]
)
def test_update_params(params: List[dict], expected_output: List[dict]):
    """Tests the update_params function, which reformats the source code type
    labels as strings. There are seven test cases for this function, which test
    for updating different parameter types.

    Args:
        params (List[dict]): Pipeline parameters. A list of dictionaries, each param is a dict containing keys:
            'name': required, str param name.
            'type': required, python primitive type.
            'description': optional, str param desc.
        expected_output (List[dict]): Expectation of whether or not the configuration is valid.
    """
    if expected_output is not None:
        assert expected_output == update_params(params=params)
    else:
        with pytest.raises(ValueError):
            assert update_params(params=params)
'''
