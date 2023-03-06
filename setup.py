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
"""Setup AutoMLOps modules"""
from setuptools import setup

setup(
    name='AutoMLOps',
    version='1.0.2',
    description='AutoMLOps is a service that generates a production-style \
        MLOps pipeline from Jupyter Notebooks.',
    url='https://github.com/GoogleCloudPlatform/automlops',
    author='Sean Rastatter',
    author_email='srastatter@google.com',
    license='Apache-2.0',
    packages=['AutoMLOps'],
    install_requires=['autoflake==2.0.0',
                      'docopt==0.6.2',
                      'ipython==7.34.0',
                      'pipreqs==0.4.11',
                      'pyflakes==3.0.1',
                      'PyYAML==5.4.1',
                      'yarg==0.1.9'],
    classifiers=[
        'Development Status :: Draft',
        'Intended Audience :: data science practitioners',
        'License :: OSI Approved :: Apache-2.0',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',])
