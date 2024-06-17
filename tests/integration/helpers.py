"""Helper functions for integration tests"""

import subprocess
import re
from google_cloud_automlops.utils.utils import (
    precheck_deployment_requirements
)


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
        raise RuntimeError(f"Error executing process. {err}") from err

def assert_successful_provisioning(defaults):
    try:
        precheck_deployment_requirements(defaults)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        # Assert False with informative error message
        assert False, f"Unexpected error with provisioning: {e}"
    else:
        # No exception occurred, assert True
        assert True

def assert_repository_exists(repository_name):
    """
    Helper function to assert that a specified repository exists.

    Args:
        repository_name: The name of the repository to check.

    Raises:
        AssertionError: If the repository doesn't exist.
    """
    args = [f"gcloud source repos list --filter={repository_name}"]
    output = subprocess.run(
        args,
        shell=True,
        capture_output=True,
        text=True,
        check=True
    ).stdout
    pattern = r"\b" + re.escape(repository_name) + r"\b"
    match = re.search(pattern, output)

    # Access the matched string using group()
    matched_repository_name = match.group() if match else None
    assert matched_repository_name == repository_name, \
           f"Repository '{repository_name}' doesn't exist."

def assert_build_trigger_exists(trigger_name, region="us-central1"):
    """
    Helper function to assert that a specified build trigger exists
    in a given region.

    Args:
        trigger_name: The name of the build trigger to check.
        region: The region where the trigger should exist.
                Defaults to "us-central1".

    Raises:
        AssertionError: If the build trigger with the given name doesn't exist
                        in the specified region.
    """
    output = subprocess.run(
        [f"gcloud builds triggers list --region={region}"],
        shell=True,
        capture_output=True,
        text=True,
        check=True
    ).stdout
    pattern = r"\b" + re.escape(trigger_name) + r"\b"
    match = re.search(pattern, output)

    # Access the matched string using group()
    matched_trigger_name = match.group() if match else None
    assert matched_trigger_name == trigger_name, \
           f"Build trigger '{trigger_name}' doesn't exist in region '{region}'."

def assert_scheduler_job_exists(scheduler_name, location="us-central1"):
    """
    Helper function to assert that a specified scheduler job exists
    in a given location.

    Args:
        job_name: The name of the scheduler job to check.
        location: The location where the job should exist.
                  Defaults to "us-central1".

    Raises:
        AssertionError: If the scheduler job with the given name doesn't exist
                        in the specified location.
    """
    output = subprocess.run(
        [f"gcloud scheduler jobs list --location={location}"],
        shell=True,
        capture_output=True,
        text=True,
        check=True
    ).stdout
    pattern = r"\b" + re.escape(scheduler_name) + r"\b"
    match = re.search(pattern, output)

    # Access the matched string using group()
    matched_scheduler_name = match.group() if match else None
    assert matched_scheduler_name == scheduler_name, \
           f"Scheduler job '{scheduler_name}' doesn't \
             exist in location '{location}'."
