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

"""Builds KFP components and pipeline."""

# pylint: disable=C0103
# pylint: disable=line-too-long

from typing import Callable, Dict, List, Optional
from AutoMLOps.Utils import BuilderUtils
from AutoMLOps.Utils.Constants import LEFT_BRACKET, RIGHT_BRACKET, NEWLINE, LICENSE, PARAMETER_VALUES_PATH, PIPELINE_JOB_SPEC_PATH
from AutoMLOps.Builder.Base import Component, Pipeline

class KFPComponent(Component):
    def __init__(self, component_spec, defaults_file):
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
        custom_code = self._component_spec['implementation']['container']['command'][-1]
        default_imports = (
            LICENSE +
            'import argparse\n'
            'import json\n'
            'import kfp\n'
            'from kfp.v2 import dsl\n'
            'from kfp.v2.components import executor\n'
            'from kfp.v2.dsl import *\n'
            'from typing import *\n'
            '\n')
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
        return default_imports + custom_code + main_func

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

class KFPPipeline(Pipeline):
    def __init__(self, custom_training_job_specs, defaults_file):
        """Instantiate Pipeline scripts object with all necessary attributes.

        Args:
            custom_training_job_specs (List[Dict]): Specifies the specs to run the training job with.
            defaults_file (str): Path to the default config variables yaml.
        """
        super().__init__(custom_training_job_specs, defaults_file)
        self.pipeline_imports = self._get_pipeline_imports()
        self.pipeline_argparse = self._get_pipeline_argparse()
        self.pipeline_runner = self._get_pipeline_runner()

    def _get_pipeline_imports(self):
        """Generates python code that imports modules and loads all custom components.

        Returns:
            str: Python pipeline_imports code.
        """
        components_list = BuilderUtils.get_components_list(full_path=False)
        gcpc_imports = (
            'from functools import partial\n'
            'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component\n')
        quote = '\''
        newline_tab = '\n    '

        # If there is a custom training job specified, write those to feed to pipeline imports
        if not self._custom_training_job_specs:
            custom_specs = ''
        else:
            custom_specs = (
                f'''    {newline_tab.join(f'{spec["component_spec"]}_custom_training_job_specs = {BuilderUtils.format_spec_dict(spec)}' for spec in self._custom_training_job_specs)}'''
                f'\n'
                f'''    {newline_tab.join(f'{spec["component_spec"]}_job_op = create_custom_training_job_op_from_component(**{spec["component_spec"]}_custom_training_job_specs)' for spec in self._custom_training_job_specs)}'''
                f'\n'
                f'''    {newline_tab.join(f'{spec["component_spec"]} = partial({spec["component_spec"]}_job_op, project={quote}{self._project_id}{quote})' for spec in self._custom_training_job_specs)}'''        
                f'\n')

        # Return standard code and customized specs
        return (
            f'''import argparse\n'''
            f'''import os\n'''
            f'''{gcpc_imports if self._custom_training_job_specs else ''}'''
            f'''import kfp\n'''
            f'''from kfp.v2 import compiler, dsl\n'''
            f'''from kfp.v2.dsl import *\n'''
            f'''from typing import *\n'''
            f'''import yaml\n'''
            f'\n'
            f'''def load_custom_component(component_name: str):\n'''
            f'''    component_path = os.path.join('components',\n'''
            f'''                                component_name,\n'''
            f'''                              'component.yaml')\n'''
            f'''    return kfp.components.load_component_from_file(component_path)\n'''
            f'\n'
            f'''def create_training_pipeline(pipeline_job_spec_path: str):\n'''
            f'''    {newline_tab.join(f'{component} = load_custom_component(component_name={quote}{component}{quote})' for component in components_list)}\n'''
            f'\n'
            f'''{custom_specs}''')

    def _get_pipeline_argparse(self):
        """Generates python code that loads default pipeline parameters from the defaults config_file.

        Returns:
            str: Python pipeline_argparse code.
        """
        return (
            '''if __name__ == '__main__':\n'''
            '''    parser = argparse.ArgumentParser()\n'''
            '''    parser.add_argument('--config', type=str,\n'''
            '''                       help='The config file for setting default values.')\n'''
            '\n'
            '''    args = parser.parse_args()\n'''
            '\n'
            '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
            '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
            '\n'
            '''    pipeline = create_training_pipeline(\n'''
            '''        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])\n''')

    def _get_pipeline_runner(self):
        """Generates python code that sends a PipelineJob to Vertex AI.

        Returns:
            str: Python pipeline_runner code.
        """
        return (
            LICENSE +
            '''import argparse\n'''
            '''import json\n'''
            '''import logging\n'''
            '''import os\n'''
            '''import yaml\n'''
            '\n'
            '''from google.cloud import aiplatform\n'''
            '\n'
            '''logger = logging.getLogger()\n'''
            '''log_level = os.environ.get('LOG_LEVEL', 'INFO')\n'''
            '''logger.setLevel(log_level)\n'''
            '\n'
            '''def run_pipeline(\n'''
            '''    project_id: str,\n'''
            '''    pipeline_root: str,\n'''
            '''    pipeline_runner_sa: str,\n'''
            '''    parameter_values_path: str,\n'''
            '''    pipeline_spec_path: str,\n'''
            '''    display_name: str = 'mlops-pipeline-run',\n'''
            '''    enable_caching: bool = False):\n'''
            '''    """Executes a pipeline run.\n'''
            '\n'
            '''    Args:\n'''
            '''        project_id: The project_id.\n'''
            '''        pipeline_root: GCS location of the pipeline runs metadata.\n'''
            '''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
            '''        parameter_values_path: Location of parameter values JSON.\n'''
            '''        pipeline_spec_path: Location of the pipeline spec JSON.\n'''
            '''        display_name: Name to call the pipeline.\n'''
            '''        enable_caching: Should caching be enabled (Boolean)\n'''
            '''    """\n'''
            '''    with open(parameter_values_path, 'r') as file:\n'''
            '''        try:\n'''
            '''            pipeline_params = json.load(file)\n'''
            '''        except ValueError as exc:\n'''
            '''            print(exc)\n'''
            '''    logging.debug('Pipeline Parms Configured:')\n'''
            '''    logging.debug(pipeline_params)\n'''
            '\n'
            '''    aiplatform.init(project=project_id)\n'''
            '''    job = aiplatform.PipelineJob(\n'''
            '''        display_name = display_name,\n'''
            '''        template_path = pipeline_spec_path,\n'''
            '''        pipeline_root = pipeline_root,\n'''
            '''        parameter_values = pipeline_params,\n'''
            '''        enable_caching = enable_caching)\n'''
            '''    logging.debug('AI Platform job built. Submitting...')\n'''
            '''    job.submit(service_account=pipeline_runner_sa)\n'''
            '''    logging.debug('Job sent!')\n'''
            '\n'
            '''if __name__ == '__main__':\n'''
            '''    parser = argparse.ArgumentParser()\n'''
            '''    parser.add_argument('--config', type=str,\n'''
            '''                        help='The config file for setting default values.')\n'''
            '''    args = parser.parse_args()\n'''
            '\n'
            '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
            '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
            '\n'
            '''    run_pipeline(project_id=config['gcp']['project_id'],\n'''
            '''                 pipeline_root=config['pipelines']['pipeline_storage_path'],\n'''
            '''                 pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],\n'''
            '''                 parameter_values_path=config['pipelines']['parameter_values_path'],\n'''
            '''                 pipeline_spec_path=config['pipelines']['pipeline_job_spec_path']) \n''')