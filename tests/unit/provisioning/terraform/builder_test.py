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
    create_data_tf_jinja,
    create_iam_tf_jinja,
    create_main_tf_jinja,
    create_outputs_tf_jinja,
    create_provider_tf_jinja,
    create_variables_tf_jinja,
    create_versions_tf_jinja,
    create_provision_resources_script_jinja
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
def test_create_data_tf_jinja(
    required_apis: List,
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    data_tf_str = create_data_tf_jinja(required_apis)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in data_tf_str
        elif not is_included:
            assert snippet not in data_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_iam_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    iam_tf_str = create_iam_tf_jinja()

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
def test_create_main_tf_jinja(
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
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    main_tf_str = create_main_tf_jinja(
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
def test_create_outputs_tf_jinja(
    artifact_repo_type: str,
    deployment_framework: str,
    pipeline_job_submission_service_type: str,
    schedule_pattern: str,
    source_repo_type: str,
    use_ci: bool,
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    main_tf_str = create_outputs_tf_jinja(
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
def test_create_provider_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    provider_tf_str = create_provider_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in provider_tf_str
        elif not is_included:
            assert snippet not in provider_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_variables_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    variables_tf_str = create_variables_tf_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in variables_tf_str
        elif not is_included:
            assert snippet not in variables_tf_str


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_create_versions_tf_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    versions_tf_str = create_versions_tf_jinja()

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
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    provision_resources_script = create_provision_resources_script_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in provision_resources_script
        elif not is_included:
            assert snippet not in provision_resources_script
