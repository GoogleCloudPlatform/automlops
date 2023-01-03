import os
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
    deploy_model = load_custom_component(component_name='deploy_model')
    train_model = load_custom_component(component_name='train_model')
    create_dataset = load_custom_component(component_name='create_dataset')
    
    @dsl.pipeline(name='training-pipeline')
    def pipeline(bq_table: str,
                 output_model_directory: str,
                 project: str,
                 region: str,
                ):
    
        dataset_task = create_dataset(
            bq_table=bq_table, 
            project=project)
    
        model_task = train_model(
            output_model_directory=output_model_directory,
            dataset=dataset_task.output)
    
        deploy_task = deploy_model(
            model=model_task.outputs["model"],
            project=project,
            region=region)
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
