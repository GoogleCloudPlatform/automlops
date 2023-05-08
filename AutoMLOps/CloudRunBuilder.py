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

"""Builds cloud_run files."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from AutoMLOps import BuilderUtils
from AutoMLOps import ScriptsBuilder

def formalize(top_lvl_name: str,
              defaults_file: str,):
    """Constructs and writes a Dockerfile, requirements.txt, and
       main.py to the cloud_run/run_pipeline directory. Also
       constructs and writes a main.py, requirements.txt, and
       pipeline_parameter_values.json to the
       cloud_run/queueing_svc directory.

    Args:
        top_lvl_name: Top directory name.
        defaults_file: Path to the default config variables yaml.
    """
    # Make new directories
    BuilderUtils.make_dirs([top_lvl_name + 'cloud_run',
                            top_lvl_name + 'cloud_run/run_pipeline',
                            top_lvl_name + 'cloud_run/queueing_svc'])

    # Initialize cloud run scripts object
    cloudrun_scripts = ScriptsBuilder.CloudRun(defaults_file)

    # Set new folders as variables
    cloudrun_base = top_lvl_name + 'cloud_run/run_pipeline'
    queueing_svc_base = top_lvl_name + 'cloud_run/queueing_svc'

    # Write cloud run dockerfile
    BuilderUtils.write_file(f'{cloudrun_base}/Dockerfile', cloudrun_scripts.dockerfile, 'w')

    # Write requirements files for cloud run base and queueing svc
    BuilderUtils.write_file(f'{cloudrun_base}/requirements.txt', cloudrun_scripts.cloudrun_base_reqs, 'w')
    BuilderUtils.write_file(f'{queueing_svc_base}/requirements.txt', cloudrun_scripts.queueing_svc_reqs, 'w')

    # Write main code files for cloud run base and queueing svc
    BuilderUtils.write_file(f'{cloudrun_base}/main.py', cloudrun_scripts.cloudrun_base, 'w')
    BuilderUtils.write_file(f'{queueing_svc_base}/main.py', cloudrun_scripts.queueing_svc, 'w')

    # Copy runtime parameters over to queueing_svc dir
    BuilderUtils.execute_process(f'''cp -r {top_lvl_name + BuilderUtils.PARAMETER_VALUES_PATH} {top_lvl_name + 'cloud_run/queueing_svc'}''', to_null=False)