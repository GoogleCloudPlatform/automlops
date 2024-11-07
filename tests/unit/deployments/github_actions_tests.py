# Copyright 2024 Google LLC. All Rights Reserved.
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
# pylint: disable=too-many-positional-arguments

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from typing import List

import pytest

from google_cloud_automlops.utils.constants import (
    COMPONENT_BASE_RELATIVE_PATH,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GITHUB_ACTIONS_TEMPLATES_PATH
)
from google_cloud_automlops.utils.utils import render_jinja


@pytest.mark.parametrize(
    '''artifact_repo_location, artifact_repo_name, naming_prefix,'''
    '''project_id, project_number, pubsub_topic_name, use_ci, source_repo_branch,'''
    '''workload_identity_provider, workload_identity_pool, workload_identity_service_account, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', True, 'automlops',
            'my-provider', 'my-pool', 'my-sa', True,
            ['id: auth',
             'id: build-push-component-base',
             'id: install-pipeline-deps',
             'id: build-pipeline-spec',
             'id: publish-to-topic', 
             'us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest',
             'gcloud pubsub topics publish my-topic --message']
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', False, 'automlops',
            'my-provider', 'my-pool', 'my-sa', True,
            ['id: build-push-component-base',
             'us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest']
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', False, 'automlops',
            'my-provider', 'my-pool', 'my-sa', False,
            ['id: install-pipeline-deps',
             'id: build-pipeline-spec',
             'id: publish-to-topic',
             'gcloud pubsub topics publish my-topic --message']
        ),
    ]
)
def test_create_github_actions_jinja(
    artifact_repo_location: str,
    artifact_repo_name: str,
    naming_prefix: str,
    project_id: str,
    project_number: str,
    pubsub_topic_name: str,
    use_ci: bool,
    source_repo_branch: str,
    workload_identity_pool: str,
    workload_identity_provider: str,
    workload_identity_service_account: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests create_github_actions_jinja, which generates content for the github actions file. 
       There are three test cases for this function:
        1. Checks that expected strings are included when use_ci=True. 
        2. Checks that expected strings are included when use_ci=False. 
        3. Checks that certain strings are not included when use_ci=False. 

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        project_id: The project ID.
        project_number: The project number.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        source_repo_branch: The branch to use in the source repository.
        use_ci: Flag that determines whether to use Cloud CI/CD.
        workload_identity_pool: Pool for workload identity federation. 
        workload_identity_provider: Provider for workload identity federation.
        workload_identity_service_account: Service account for workload identity federation. 
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """

    template_file = import_files(GITHUB_ACTIONS_TEMPLATES_PATH) / 'github_actions.yaml.j2'
    github_actions_config = render_jinja(
        template_path=template_file,
        artifact_repo_location=artifact_repo_location,
        artifact_repo_name=artifact_repo_name,
        component_base_relative_path=COMPONENT_BASE_RELATIVE_PATH,
        generated_license=GENERATED_LICENSE,
        generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
        naming_prefix=naming_prefix,
        project_id=project_id,
        project_number=project_number,
        pubsub_topic_name=pubsub_topic_name,
        source_repo_branch=source_repo_branch,
        use_ci=use_ci,
        workload_identity_pool=workload_identity_pool,
        workload_identity_provider=workload_identity_provider,
        workload_identity_service_account=workload_identity_service_account
    )

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in github_actions_config
        elif not is_included:
            assert snippet not in github_actions_config
