import subprocess
import os
import logging
import time
from google.cloud import aiplatform
import yaml

def execute_process(command: str, to_null: bool):
        """Executes an external shell process.

        Args:
            command: The string of the command to execute.
            to_null: Determines where to send output.
        Raises:
            Exception: If an error occurs in executing the script.
        """
        stdout = subprocess.DEVNULL if to_null else None
        try:
            subprocess.run([command], shell=True, check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            raise RuntimeError(f'Error executing process. {err}') from err

def string_execute_process(command: str, to_null: bool = False) -> str:
    """Executes an external shell process and captures its output.

    Args:
        command: The string of the command to execute.
        to_null: If True, output will be sent to /dev/null; otherwise, it's captured.

    Returns:
        The combined standard output (stdout) and standard error (stderr) as a string.

    Raises:
        RuntimeError: If an error occurs during command execution.
    """

    try:
        result = subprocess.run(
            command,
            shell=True,  # Interpret the command as a shell command
            check=True,   # Raise an exception if the command returns a non-zero exit code
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True,     # Decode output as text (Python 3.7+)
        )

        if to_null:
            return ""  # Return an empty string if output is directed to /dev/null
        else:
            return result.stdout  # Return the captured output as a string

    except subprocess.CalledProcessError as err:
        raise RuntimeError(f'Error executing process: {err}') from err

def load_defaults(file_path="defaults.yaml"):
    """Loads resource names from a YAML file.

    Args:
        file_path (str, optional): Path to the YAML file.

    Returns:
        dict: A dictionary containing the resource names.
    """
    with open(file_path, "r") as file:
        defaults = yaml.safe_load(file)
    return defaults

def teardown_gcloud_artifact_registry(project_id, artifact_repo_location, artifact_repo_name="dry-beans-dt-inferencing-artifact-registry"): 
    """Deletes a Google Cloud artifact registry if it exists.

    Args:
        project_id: The ID of the Google Cloud project.
        artifact_repo_name: The name of the bucket to delete.
    """
    artifact_list = string_execute_process(f'gcloud artifacts repositories list --project={project_id} --location={artifact_repo_location}', False)
    if artifact_repo_name in artifact_list:
        print("This is the artifact list: ", artifact_list)
        outputs = string_execute_process(f"gcloud artifacts repositories delete {artifact_repo_name} --location={artifact_repo_location} --quiet")
        print(outputs)
    else:
        print(f"The artifact registry {artifact_repo_name} doesn't exist in {artifact_repo_location}")

from google.cloud import storage
def teardown_gcs_bucket(project_id, bucket_name):
    """Deletes a Google Cloud Storage bucket if it exists.

    Args:
        project_id: The ID of the Google Cloud project.
        bucket_name: The name of the bucket to delete.
    """
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.get_bucket(bucket_name)  
        bucket.delete(force=True) 
        print(f"Bucket '{bucket_name}' deleted successfully.")
    except:
        print(f"Bucket '{bucket_name}' does not exist.")

def teardown_cloud_source_repository(project_id, repo_name):
    """Deletes a Cloud Source Repository if it exists, using gcloud.

    Args:
        project_id: The ID of the Google Cloud project.
        repo_name: The name of the repository to delete.
    """
    existing_repos = string_execute_process(f'gcloud source repos list --project={project_id}')
    if repo_name in existing_repos:
        
        try:
            delete_output = string_execute_process(f"gcloud source repos delete {repo_name} --project={project_id} --quiet")
            print(f"Deleted Cloud Source Repository '{repo_name}' successfully.")
            print("Details:", delete_output)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting repository '{repo_name}': {e.stderr}")
    
    else:
        print(f"Cloud Source Repository '{repo_name}' does not exist in project '{project_id}'.")

def teardown_pubsub_topic(project_id, topic_name):
    """Deletes a Pub/Sub topic if it exists, using gcloud.

    Args:
        project_id: The ID of the Google Cloud project.
        topic_name: The name of the topic to delete.
    """
    
    existing_topics = string_execute_process(f'gcloud pubsub topics list --project={project_id}')
    if topic_name in existing_topics:
        try:
            delete_output = string_execute_process(f"gcloud pubsub topics delete {topic_name} --project={project_id}")
            print(f"Deleted Pub/Sub topic '{topic_name}' successfully.")
            print("Details:", delete_output)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting topic '{topic_name}': {e.stderr}")
    else:
        print(f"Pub/Sub topic '{topic_name}' does not exist in project '{project_id}'.")

def undeploy_cloud_function(project_id, region, function_name):
    """Args:
        project_id: The ID of the Google Cloud project.
        region: The region where the Cloud Function is deployed.
        function_name: The name of the Cloud Function to undeploy.
    """

    existing_functions = string_execute_process(f'gcloud functions list --project={project_id} --regions={region}')
    if function_name in existing_functions:

        try:
            delete_output = string_execute_process(
                f"gcloud functions delete {function_name} --project={project_id} --region={region} --quiet"
            )
            print(f"Deleted Cloud Function '{function_name}' successfully.")
            print("Details:", delete_output)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting Cloud Function '{function_name}': {e.stderr}")

    else:
        print(f"Cloud Function '{function_name}' does not exist in region '{region}'.")

def undeploy_cloud_build_trigger(project_id, region, trigger_name):
    """Args:
        project_id: The ID of the Google Cloud project.
        region: The region where the Cloud Build trigger is located.
        trigger_name: The name of the Cloud Build trigger to delete.
    """

    existing_triggers = string_execute_process(f'gcloud beta builds triggers list --project={project_id} --region={region}')
    
    if trigger_name in existing_triggers:

        try:
            delete_output = string_execute_process(
                f"gcloud beta builds triggers delete {trigger_name} --project={project_id} --region={region} --quiet"
            )
            print(f"Deleted Cloud Build trigger '{trigger_name}' successfully.")
            print("Details:", delete_output)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting Cloud Build trigger '{trigger_name}': {e.stderr}")

    else:
        print(f"Cloud Build trigger '{trigger_name}' does not exist in region '{region}'.")

def undeploy_cloud_scheduler_job(project_id, region, job_name):
    """Undeploys a Google Cloud Scheduler job using gcloud.

    Args:
        project_id: The ID of the Google Cloud project.
        region: The region where the Cloud Scheduler job is located.
        job_name: The name of the Cloud Scheduler job to delete.
    """

    existing_jobs = string_execute_process(f'gcloud scheduler jobs list --project={project_id} --location={region}')
    
    if f"ID\t{job_name}" in existing_jobs or f"ID\t{job_name} " in existing_jobs:

        try:
            delete_output = string_execute_process(
                f"gcloud scheduler jobs delete {job_name} --project={project_id} --location={region} --quiet"
            )
            print(f"Deleted Cloud Scheduler job '{job_name}' successfully.")
            print("Details:", delete_output)
        except subprocess.CalledProcessError as e:
            print(f"Error deleting Cloud Scheduler job '{job_name}': {e.stderr}")

    else:
        print(f"Cloud Scheduler job '{job_name}' does not exist in region '{region}'.")

AMO_resource_values = load_defaults()

teardown_gcloud_artifact_registry(project_id=AMO_resource_values["project_id"], 
artifact_repo_location=AMO_resource_values["artifact_repo_location"],
artifact_repo_name=AMO_resource_values["artifact_repo_name"]
)

teardown_gcs_bucket(
    project_id=AMO_resource_values["project_id"],
    bucket_name=AMO_resource_values["storage_bucket_name"]
)

teardown_cloud_source_repository(
    project_id=AMO_resource_values["project_id"],
    repo_name=AMO_resource_values["source_repository_name"]
)

teardown_pubsub_topic(
    project_id=AMO_resource_values["project_id"],
    topic_name=AMO_resource_values["pubsub_topic_name"]
)

undeploy_cloud_function(
    project_id=AMO_resource_values["project_id"],
    region=AMO_resource_values["pipeline_job_submission_service_location"],
    function_name=AMO_resource_values["pipeline_job_submission_service_name"]
)

undeploy_cloud_build_trigger(
    project_id=AMO_resource_values["project_id"],
    region=AMO_resource_values["build_trigger_location"],
    trigger_name=AMO_resource_values["build_trigger_name"]
)

undeploy_cloud_scheduler_job(
    project_id=AMO_resource_values["project_id"],
    region=AMO_resource_values["schedule_location"],
    job_name=AMO_resource_values["schedule_name"]
)











    
