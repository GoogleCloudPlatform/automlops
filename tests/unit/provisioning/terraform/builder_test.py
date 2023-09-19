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

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

from typing import List

import pytest

from google_cloud_automlops.utils.constants import GENERATED_LICENSE
from google_cloud_automlops.provisioning.terraform.builder import (
    create_environment_data_tf_jinja,
    create_environment_iam_tf_jinja,
    create_environment_main_tf_jinja,
    create_environment_outputs_tf_jinja,
    create_environment_provider_tf_jinja,
    create_environment_variables_tf_jinja,
    create_environment_versions_tf_jinja,
    create_provision_resources_script_jinja,
    create_state_bucket_variables_tf_jinja,
    create_state_bucket_main_tf_jinja
)


@pytest.mark.parametrize(
    'required_apis, is_included, expected_output_snippets',
    [
        (
            ['apiA', 'apiB'], True,
            [GENERATED_LICENSE, 'archive_cloud_functions_submission_service',
             'enable_apis = [\n'
             '      "apiA",\n'
             '      "apiB",\n'
             '    ]'
            ]
        )
    ]
)
def test_create_environment_data_tf_jinja(
    required_apis: List,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_data_tf_jinja, which generates code for environment/data.tf, 
       the terraform hcl script that contains terraform remote backend and org project details. 
       There is one test case for this function:
        1. Checks for the apache license and relevant terraform blocks.

    Args:
        required_apis: List of APIs that are required to run the service.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    data_tf_str = create_environment_data_tf_jinja(required_apis)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in data_tf_str
        elif not is_included:
            assert snippet not in data_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_environment_iam_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_iam_tf_jinja, which generates code for environment/iam.tf, the terraform hcl 
       script that contains service accounts iam bindings for project's environment. 
       There is one test case for this function:
        1. Checks for the apache license.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    iam_tf_str = create_environment_iam_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in iam_tf_str
        elif not is_included:
            assert snippet not in iam_tf_str


@pytest.mark.parametrize(
    '''artifact_repo_type, deployment_framework, naming_prefix,'''
    '''pipeline_job_submission_service_type, schedule_pattern,'''
    '''source_repo_type, use_ci, vpc_connector, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-functions', '0 12 * * *',
            'cloud-source-repositories', True, 'my-vpc-connector', True,
            ['resource "google_artifact_registry_repository"',
             'resource "google_storage_bucket"',
             'resource "google_sourcerepo_repository"',
             'resource "google_pubsub_topic"',
             'resource "google_storage_bucket_object"',
             'resource "google_cloudfunctions_function"',
             'vpc_connector         =',
             'resource "google_cloudbuild_trigger"',
             'resource "google_cloud_scheduler_job"']
        ),
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-run', '0 12 * * *',
            'cloud-source-repositories', True, 'my-vpc-connector', True,
            ['resource "google_artifact_registry_repository"',
             'resource "google_storage_bucket"',
             'resource "google_sourcerepo_repository"',
             'resource "null_resource" "build_and_push_submission_service"',
             'module "cloud_run"',
             'run.googleapis.com/vpc-access-connector',
             'module "pubsub"',
             'resource "google_cloudbuild_trigger"',
             'resource "google_cloud_scheduler_job"']
        ),
        (
            'some-other-repo', 'cloud-build', 'my-prefix',
            'cloud-functions', '0 12 * * *',
            'cloud-source-repositories', True, 'No VPC Specified', False,
            ['resource "google_artifact_registry_repository"', 'vpc_connector         =']
        ),
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-run', '0 12 * * *',
            'cloud-source-repositories', True, 'No VPC Specified', False,
            ['run.googleapis.com/vpc-access-connector']
        ),
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-functions', 'No Schedule Specified',
            'cloud-source-repositories', True, 'No VPC Specified', False,
            ['resource "google_cloud_scheduler_job"']
        ),
        (
            'artifact-registry', 'some-deployment-framework', 'my-prefix',
            'cloud-functions', 'No Schedule Specified',
            'cloud-source-repositories', True, 'No VPC Specified', False,
            ['resource "google_cloudbuild_trigger"']
        ),
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-functions', 'No Schedule Specified',
            'some-other-code-repo', True, 'No VPC Specified', False,
            ['resource "google_sourcerepo_repository"', 'resource "google_cloudbuild_trigger"']
        ),
        (
            'artifact-registry', 'cloud-build', 'my-prefix',
            'cloud-functions', 'No Schedule Specified',
            'some-other-code-repo', False, 'No VPC Specified', False,
            ['resource "null_resource" "build_and_push_submission_service"',
             'module "cloud_run"',
             'module "pubsub"',
             'resource "google_pubsub_topic"',
             'resource "google_storage_bucket_object"',
             'resource "google_cloudfunctions_function"',
             'resource "google_cloudbuild_trigger"',
             'resource "google_cloud_scheduler_job"']
        ),
    ]
)
def test_create_environment_main_tf_jinja(
    artifact_repo_type: str,
    deployment_framework: str,
    naming_prefix: str,
    pipeline_job_submission_service_type: str,
    schedule_pattern: str,
    source_repo_type: str,
    use_ci: bool,
    vpc_connector: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_main_environment_tf_jinja, which generates code for environment/main.tf, the terraform hcl 
       script that contains terraform resources configs to deploy resources in the project.
       There are eight test cases for this function:
        1. Checks for relevant terraform blocks when using the following tooling:
            artifact-registry, cloud-build, cloud-functions, cloud scheduler, cloud-source-repositories, and a vpc connector
        2. Checks for relevant terraform blocks when using the following tooling:
            artifact-registry, cloud-build, cloud-run, cloud scheduler, cloud-source-repositories, and a vpc connector
        3. Checks that the artifact-registry terraform block is not included when not using artifact-registry.
        4. Checks that the vpc-connector element is not included when not using a vpc connector.
        5. Checks that the cloud scheduler terraform block is not included when not using a cloud schedule.
        6. Checks that the cloud build trigger terraform block is not included when not using cloud-build.
        7. Checks that the cloud source repositories and cloud build trigger terraform blocks are not included when not using cloud-source-repositories.
        8. Checks for that CI/CD infra terraform blocks are not included when use_ci=False.
            
    Args:
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    main_tf_str = create_environment_main_tf_jinja(
        artifact_repo_type=artifact_repo_type,
        deployment_framework=deployment_framework,
        naming_prefix=naming_prefix,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        schedule_pattern=schedule_pattern,
        source_repo_type=source_repo_type,
        use_ci=use_ci,
        vpc_connector=vpc_connector)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in main_tf_str
        elif not is_included:
            assert snippet not in main_tf_str


@pytest.mark.parametrize(
    '''artifact_repo_type, deployment_framework,'''
    '''pipeline_job_submission_service_type, schedule_pattern,'''
    '''source_repo_type, use_ci, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'artifact-registry', 'cloud-build',
            'cloud-functions', '0 12 * * *',
            'cloud-source-repositories', True, True,
            ['output "enabled_apis"',
             'output "create_pipeline_job_runner_service_account_email"',
             'output "create_artifact_registry"',
             'output "create_storage_bucket"',
             'output "create_storage_bucket_names"',
             'output "create_cloud_source_repository"',
             'output "create_pubsub_topic"',
             'output "create_cloud_function"',
             'output "create_cloud_build_trigger"',
             'output "create_cloud_scheduler_name"',
             'output "create_cloud_scheduler_job"']
        ),
        (
            'artifact-registry', 'cloud-build',
            'cloud-run', '0 12 * * *',
            'cloud-source-repositories', True, True,
            ['output "enabled_apis"',
             'output "create_pipeline_job_runner_service_account_email"',
             'output "create_artifact_registry"',
             'output "create_storage_bucket"',
             'output "create_storage_bucket_names"',
             'output "create_cloud_source_repository"',
             'output "cloud_run_id"',
             'output "create_pubsub_subscription"',
             'output "create_cloud_build_trigger"',
             'output "create_cloud_scheduler_name"',
             'output "create_cloud_scheduler_job"']
        ),
        (
            'some-other-repo', 'cloud-build',
            'cloud-functions', '0 12 * * *',
            'cloud-source-repositories', True, False,
            ['output "create_artifact_registry"']
        ),
        (
            'artifact-registry', 'cloud-build',
            'cloud-run', '0 12 * * *',
            'cloud-source-repositories', True, False,
            ['output "create_cloud_function"']
        ),
        (
            'artifact-registry', 'cloud-build',
            'cloud-functions', 'No Schedule Specified',
            'cloud-source-repositories', True, False,
            ['output "create_cloud_scheduler_name"',
             'output "create_cloud_scheduler_job"']
        ),
        (
            'artifact-registry', 'some-deployment-framework',
            'cloud-functions', 'No Schedule Specified',
            'cloud-source-repositories', True, False,
            ['output "create_cloud_build_trigger"']
        ),
        (
            'artifact-registry', 'cloud-build',
            'cloud-functions', 'No Schedule Specified',
            'some-other-code-repo', True, False,
            ['output "create_cloud_source_repository"',
             'output "create_cloud_build_trigger"']
        ),
        (
            'artifact-registry', 'cloud-build',
            'cloud-functions', 'No Schedule Specified',
            'some-other-code-repo', False, False,
            ['resource "null_resource" "build_and_push_submission_service"',
             'output "cloud_run_id"'
             'output "create_pubsub_subscription"',
             'output "create_pubsub_topic"',
             'output "create_cloud_function"',
             'output "create_cloud_build_trigger"',
             'output "create_cloud_scheduler_name"',
             'output "create_cloud_scheduler_job" ']
        ),
    ]
)
def test_create_environment_outputs_tf_jinja(
    artifact_repo_type: str,
    deployment_framework: str,
    pipeline_job_submission_service_type: str,
    schedule_pattern: str,
    source_repo_type: str,
    use_ci: bool,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_outputs_tf_jinja, which gnerates code for environment/outputs.tf, the terraform hcl
       script that contains outputs from project's environment.
       There are eight test cases for this function:
        1. Checks for relevant terraform output blocks when using the following tooling:
            artifact-registry, cloud-build, cloud-functions, cloud scheduler, and cloud-source-repositories
        2. Checks for relevant terraform output blocks when using the following tooling:
            artifact-registry, cloud-build, cloud-run, cloud scheduler, and cloud-source-repositories
        3. Checks that the artifact-registry terraform output block is not included when not using artifact-registry.
        4. Checks that the cloud functions terraform output block is not included when using cloud-run.
        5. Checks that the cloud scheduler terraform output blocks are not included when not using a cloud schedule.
        6. Checks that the cloud build trigger terraform output block is not included when not using cloud-build.
        7. Checks that the cloud source repositories and cloud build trigger output blocks are not included when not using cloud-source-repositories.
        8. Checks for that CI/CD infra terraform output blocks are not included when use_ci=False.
            
    Args:
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        use_ci: Flag that determines whether to use Cloud CI/CD.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    main_tf_str = create_environment_outputs_tf_jinja(
        artifact_repo_type=artifact_repo_type,
        deployment_framework=deployment_framework,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        schedule_pattern=schedule_pattern,
        source_repo_type=source_repo_type,
        use_ci=use_ci)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in main_tf_str
        elif not is_included:
            assert snippet not in main_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_environment_provider_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_provider_tf_jinja, which generates code for environment/provider.tf, the terraform hcl
       script that contains teraform providers used to deploy project's environment.
       There is one test case for this function:
        1. Checks for the apache license.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    provider_tf_str = create_environment_provider_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in provider_tf_str
        elif not is_included:
            assert snippet not in provider_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_environment_variables_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_variables_tf_jinja, which generates code for environment/variables.tf,
       the terraform hcl script that contains variables used to deploy project's environment.
       There is one test case for this function:
        1. Checks for the apache license.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    variables_tf_str = create_environment_variables_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in variables_tf_str
        elif not is_included:
            assert snippet not in variables_tf_str


@pytest.mark.parametrize(
    'storage_bucket_name, is_included, expected_output_snippets',
    [('my-storage-bucket', True, [GENERATED_LICENSE, 'bucket =  "my-storage-bucket-bucket-tfstate"'])]
)
def test_create_environment_versions_tf_jinja(
    storage_bucket_name: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_environment_versions_tf_jinja, which generates code for environment/versions.tf,
       the terraform hcl script that contains teraform version information.
       There is one test case for this function:
        1. Checks for the apache license and state file storage_bucket backend.

    Args:
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    versions_tf_str = create_environment_versions_tf_jinja(storage_bucket_name=storage_bucket_name)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in versions_tf_str
        elif not is_included:
            assert snippet not in versions_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, '#!/bin/bash'])]
)
def test_create_provision_resources_script_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_provision_resources_script_jinja, which generates code for provision_resources.sh
       which sets up the project's environment using terraform.
       There is one test case for this function:
        1. Checks for the apache license and the Bash shebang.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    provision_resources_script = create_provision_resources_script_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in provision_resources_script
        elif not is_included:
            assert snippet not in provision_resources_script


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_state_bucket_variables_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_state_bucket_variables_tf_jinja, which generates code for state_bucket/variables.tf,
       the terraform hcl script that contains variables used for the state_bucket.
       There is one test case for this function:
        1. Checks for the apache license.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    variables_tf_str = create_state_bucket_variables_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in variables_tf_str
        elif not is_included:
            assert snippet not in variables_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_state_bucket_main_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_main_state_bucket_tf_jinja, which generates code for state_bucket/main.tf, the terraform hcl 
       script that contains terraform resources configs to create the state_bucket.
       There are eight test cases for this function:
        1. Checks for the apache license.
            
    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    main_tf_str = create_state_bucket_main_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in main_tf_str
        elif not is_included:
            assert snippet not in main_tf_str
