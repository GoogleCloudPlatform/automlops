from . import PipelineBuilder, BuilderUtils
import pytest

def test_formalize():
    assert True
    
def test_get_pipeline_imports(mocker):
    mocker.patch('AutoMLOps.BuilderUtils.get_components_list',
                 return_value=['my_path1.yml', 'my_path2.yml', 'my_path3.yml'])
    
    expected = (
        f'''import os\n'''
        f'''import argparse\n'''
        f'''import yaml\n'''
        f'''import kfp\n'''
        f'''from kfp.v2 import compiler, dsl\n'''
        f'''from kfp.v2.dsl import pipeline, component, Artifact, Dataset, Input, Metrics, Model, Output, InputPath, OutputPath\n'''
        f'''from kfp.v2.compiler import compiler\n'''
        f'\n'
        f'''def load_custom_component(component_name: str):\n'''
        f'''    component_path = os.path.join('components',\n'''
        f'''                                component_name,\n'''
        f'''                              'component.yaml')\n'''
        f'''    return kfp.components.load_component_from_file(component_path)\n'''
        f'\n'
        f'''def create_training_pipeline(pipeline_job_spec_path: str):\n'''
        f'''    my_path1.yml = load_custom_component(component_name=\'my_path1.yml\')\n'''
        f'''    my_path2.yml = load_custom_component(component_name=\'my_path2.yml\')\n'''
        f'''    my_path3.yml = load_custom_component(component_name=\'my_path3.yml\')'''
        f'\n')
    
    assert expected == PipelineBuilder.get_pipeline_imports()
    
def test_get_pipeline_argparse():
    
    expected = (
        '''    compiler.Compiler().compile(\n'''
        '''        pipeline_func=pipeline,\n'''
        '''        package_path=pipeline_job_spec_path)\n'''
        '\n'
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
        '''        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])\n'''
        )
    
    assert expected == PipelineBuilder.get_pipeline_argparse()
    
def test_get_pipeline_runner():
    
    expected = (
        BuilderUtils.LICENSE +
        '''import argparse\n'''
        '''import json\n'''
        '''import os\n'''
        '''import yaml\n'''
        '''import logging\n'''
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
        '''                 pipeline_spec_path=config['pipelines']['pipeline_job_spec_path']) \n'''
        )
    
    assert expected == PipelineBuilder.get_pipeline_runner()
    
def test_create_pipeline_scaffold():
    assert True
    
def test_get_pipeline_scaffold():
    assert True