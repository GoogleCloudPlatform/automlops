import json
import os

class PipelineBuilder:
    def __init__(self):
        self.components_dir = ""
        self.pipeline_file = ""
        self.pipeline_runner_file = ""

    def get_components_list(self):
        elements = os.listdir(self.components_dir)
        try:
            elements.remove('.DS_Store')
        except ValueError:
            pass
        return elements
    
    def get_pipeline_imports(self, components_list):
        components_list.remove('component_base')
        newline = '\n    '
        quote = '\''
        return f"""import os
import argparse
import yaml
import kfp
from kfp.v2 import compiler, dsl
from kfp.v2.dsl import pipeline, component, Artifact, Dataset, Input, Metrics, Model, Output, InputPath, OutputPath
from kfp.v2.compiler import compiler        
        
def load_custom_component(component_name: str):
    component_path = os.path.join('components',
                                   component_name,
                                  'component.yaml')
    return kfp.components.load_component_from_file(component_path)

def create_training_pipeline(pipeline_job_spec_path: str):
    {newline.join(f"{component} = load_custom_component(component_name={quote}{component}{quote})" for component in components_list)}
"""

    def get_pipeline_argparse(self):
        return f"""
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_job_spec_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                        help='The config file for setting default values.')

    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as config_file:
      config = yaml.load(config_file, Loader=yaml.FullLoader)

    pipeline = create_training_pipeline(
        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])
"""
    def get_pipeline_runner(self):
        triple_quotes = '\"\"\"'
        return f"""import argparse
import json
import os
import yaml
import logging

from google.cloud import aiplatform

logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

SERVICE_ACCOUNT = ''

def run_pipeline(
    project_id: str,
    pipeline_root: str,
    parameter_values_path: str,
    pipeline_spec_path: str,
    display_name: str = 'mlops-pipeline-run',
    enable_caching: bool = False):
    {triple_quotes}Executes a pipeline run.
    Args:
      project_id: The project_id.
      pipeline_root: GCS location of the pipeline runs metadata.
      parameter_values_path: Location of parameter values JSON.
      pipeline_spec_path: Location of the pipeline spec JSON.
      display_name: Name to call the pipeline.
      enable_caching: Should caching be enabled (Boolean)
    {triple_quotes}
    with open(parameter_values_path, 'r') as file:
      try:
          pipeline_params = json.load(file)
      except ValueError as exc:
          print(exc)
    logging.debug('Pipeline Parms Configured:')
    logging.debug(pipeline_params)

    aiplatform.init(project=project_id)
    job = aiplatform.PipelineJob(
      display_name = display_name,
      template_path = pipeline_spec_path,
      pipeline_root = pipeline_root,
      parameter_values = pipeline_params,
      enable_caching = enable_caching
    )
    logging.debug('AI Platform job built. Submitting...')
    #job.submit(service_account=SERVICE_ACCOUNT)
    job.submit()
    logging.debug('Job sent!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                        help='The config file for setting default values.')
    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as config_file:
      config = yaml.load(config_file, Loader=yaml.FullLoader)

    run_pipeline(project_id=config['gcp']['project_id'],
                 pipeline_root=config['pipelines']['pipeline_storage_path'],
                 parameter_values_path=config['pipelines']['parameter_values_path'],
                 pipeline_spec_path=config['pipelines']['pipeline_job_spec_path']) 
"""

    def formalize(self, pipeline_parameter_values, parameter_values_path, top_lvl_name):
        self.components_dir = top_lvl_name + 'components'
        self.pipeline_file = top_lvl_name + 'pipelines/pipeline.py'
        self.pipeline_runner_file = top_lvl_name + 'pipelines/pipeline_runner.py'
        # construct pipeline.py
        components_list = self.get_components_list()
        pipeline_top = self.get_pipeline_imports(components_list)
        pipeline_bottom = self.get_pipeline_argparse()

        with open(self.pipeline_file, "r+") as file:
            data = file.read()
            file.seek(0, 0)
            file.write(pipeline_top)
            for line in data.splitlines():
                file.write('    ' + line + '\n')
            file.write(pipeline_bottom)
        file.close()
        # construct pipeline_runner.py
        with open(self.pipeline_runner_file, "w+") as file:
            file.write(self.get_pipeline_runner())
        file.close()
        #construct pipeline_parameter_values.json
        serialized_params = json.dumps(pipeline_parameter_values, indent=4)
        with open(top_lvl_name + parameter_values_path, "w+") as file:
            file.write(serialized_params)
        file.close()