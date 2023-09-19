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
"""
AutoMLOps

AutoMLOps is a service that generates a production-style MLOps pipeline
from Jupyter Notebooks. The tool currently operates as a local package
import, with the end goal of becoming a Jupyter plugin to Vertex
Workbench managed notebooks. The tool will generate yaml-component
definitions, complete with Dockerfiles and requirements.txts for all
Kubeflow components defined in a notebook. It will also generate a
series of directories to support the creation of Vertex Pipelines.
"""
# pylint: disable=invalid-name
__version__ = '1.2.0'
__author__ = 'Sean Rastatter'
__credits__ = 'Google'
