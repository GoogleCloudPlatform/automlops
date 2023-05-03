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

"""Builds pipeline files."""

# pylint: disable=C0103
# pylint: disable=line-too-long

import json
from typing import Callable, Dict, List, Optional

from AutoMLOps import BuilderUtils
from AutoMLOps import ScriptsBuilder

DEFAULT_PIPELINE_NAME = 'automlops-pipeline'

def formalize(custom_training_job_specs: List[Dict],
              defaults_file: str,
              pipeline_parameter_values: dict,
              top_lvl_name: str):
    """Constructs and writes pipeline.py, pipeline_runner.py, and pipeline_parameter_values.json files.
        pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.

    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        defaults_file: Path to the default config variables yaml.
        pipeline_parameter_values: Dictionary of runtime parameters for the PipelineJob.
        top_lvl_name: Top directory name.
    Raises:
        Exception: If an error is encountered reading/writing to a file.
    """
    # Set paths
    pipeline_file = top_lvl_name + 'pipelines/pipeline.py'
    pipeline_runner_file = top_lvl_name + 'pipelines/pipeline_runner.py'
    pipeline_params_file = top_lvl_name + BuilderUtils.PARAMETER_VALUES_PATH

    # Initializes pipeline scripts builder
    pipeline_scripts = ScriptsBuilder.Pipeline(custom_training_job_specs, defaults_file)
    try:
        with open(pipeline_file, 'r+', encoding='utf-8') as file:
            pipeline_scaffold = file.read()
            file.seek(0, 0)
            file.write(BuilderUtils.LICENSE)
            file.write(pipeline_scripts.pipeline_imports)
            for line in pipeline_scaffold.splitlines():
                file.write('    ' + line + '\n')
            file.write(pipeline_scripts.pipeline_argparse)
        file.close()
    except OSError as err:
        raise OSError(f'Error interacting with file. {err}') from err

    # Construct pipeline_runner.py
    BuilderUtils.write_file(pipeline_runner_file, pipeline_scripts.pipeline_runner, 'w+')

    # Construct pipeline_parameter_values.json
    serialized_params = json.dumps(pipeline_parameter_values, indent=4)
    BuilderUtils.write_file(pipeline_params_file, serialized_params, 'w+')

def create_pipeline_scaffold(func: Optional[Callable] = None,
                             *,
                             name: Optional[str] = None,
                             description: Optional[str] = None):
    """Creates a temporary pipeline scaffold which will
       be used by the formalize function.

    Args:
        func: The python function to create a pipeline from. The function
            should have type annotations for all its arguments, indicating how
            it is intended to be used (e.g. as an input/output Artifact object,
            a plain parameter, or a path to a file).
        name: The name of the pipeline.
        description: Short description of what the pipeline does.
    """
    pipeline_scaffold = (
        f'''@dsl.pipeline'''
        f'''(\n    name='{DEFAULT_PIPELINE_NAME if not name else name}',\n'''
        f'''    description='{description if description else ''}',\n'''
        f''')\n'''
        f'''{BuilderUtils.get_function_source_definition(func)}'''
        f'''\n'''
        f'''compiler.Compiler().compile(\n'''
        f'''    pipeline_func={func.__name__},\n'''
        f'''    package_path=pipeline_job_spec_path)\n'''
        f'''\n'''
    )
    BuilderUtils.make_dirs([BuilderUtils.TMPFILES_DIR]) # if it doesn't already exist
    BuilderUtils.write_file(BuilderUtils.PIPELINE_TMPFILE, pipeline_scaffold, 'w')
