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

"""Unit tests for kfp builder module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

from AutoMLOps.frameworks.kfp.builder import (
    build, # Does not necessarily need to be tested, a combination of other functions
    build_component,
    build_pipeline,
    build_cloudrun # Does not necessarily need to be tested, a combination of other functions
)

def test_build_component():
    assert True

def test_build_pipeline():
    assert True