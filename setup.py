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
from setuptools import find_packages
from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as file:
    readme_contents = file.read()

setup(
    name='google-cloud-automlops',
    version='1.1.4',
    description='AutoMLOps is a service that generates a production-style \
        MLOps pipeline from Jupyter Notebooks.',
    long_description=readme_contents,
    long_description_content_type='text/markdown',
    url='https://github.com/GoogleCloudPlatform/automlops',
    author='Sean Rastatter',
    author_email='srastatter@google.com',
    license='Apache-2.0',
    packages=find_packages(),
    install_requires=['docopt==0.6.2',
                      'docstring-parser==0.15',
                      'pipreqs==0.4.11',
                      'PyYAML==5.4.1',
                      'yarg==0.1.9'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',])
