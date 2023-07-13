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

"""Sets global enums."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from enum import Enum


class Provider(Enum):
    """Enum representing the available providers for infrastructure management."""

    TERRAFORM = 'terraform'
    PULUMI = 'pulumi'


class PulumiRuntime(Enum):
    """Enum representing the available pulumi runtimes."""

    PYTHON = 'python'
    TYPESCRIPT = 'typescript'
    GO = 'go'
