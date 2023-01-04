import argparse
import json
from kfp.v2.components import executor
import json
from google.cloud import aiplatform

def deploy_model(
    model_directory: str,
    project_id: str,
    region: str,
):
    """Trains a decision tree on the training data.

    Args:
        model_directory: GS location of saved model.,
        project_id: Project_id.,
        region: Region.,
    """    
    
    aiplatform.init(project=project_id, location=region)
    deployed_model = aiplatform.Model.upload(
        display_name="beans-model-pipeline",
        artifact_uri = model_directory,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest"
    )
    endpoint = deployed_model.deploy(machine_type="n1-standard-4")

def main():
    """Main executor."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--executor_input', type=str)
    parser.add_argument('--function_to_execute', type=str)

    args, _ = parser.parse_known_args()
    executor_input = json.loads(args.executor_input)
    function_to_execute = globals()[args.function_to_execute]

    executor.Executor(
        executor_input=executor_input,
        function_to_execute=function_to_execute).execute()

if __name__ == '__main__':
    main()
