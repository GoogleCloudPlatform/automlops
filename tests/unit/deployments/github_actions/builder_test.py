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

from google_cloud_automlops.deployments.github_actions.builder import create_github_actions_jinja


@pytest.mark.parametrize(
    '''artifact_repo_location, artifact_repo_name, naming_prefix,'''
    '''project_id, project_number, pubsub_topic_name, use_ci, workload_identity_provider, '''
    ''' workload_identity_pool, workload_identity_service_account, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', 'my-provider',
            'my-pool', 'my-sa', True, True,
            ['id: auth',
             'id: build-push-component-base',
             'id: install-pipeline-deps',
             'id: build-pipeline-spec',
             'id: publish-to-topic', 
             'us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest',
             'gcloud pubsub topics publish my-topic --message'
             ]
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', 'my-provider',
            'my-pool', 'my-sa', True, True,
            ['id: build-push-component-base',
             'us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest']
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-project-number', 'my-topic', 'my-provider',
            'my-pool', 'my-sa', True, True,
            ['id: build-push-component-base',
             'id: install-pipeline-deps',
             'id: build-pipeline-spec',
             'id: publish-to-topic',
             'us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest',
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
    is_included: bool,
    workload_identity_pool: str,
    workload_identity_provider: str,
    workload_identity_service_account: str,
    expected_output_snippets: List[str]):
    """Tests the update_params function, which reformats the source code type
    """

    github_actions_config = create_github_actions_jinja(
        artifact_repo_location,
        artifact_repo_name,
        naming_prefix,
        project_id,
        project_number,
        pubsub_topic_name,
        use_ci,
        workload_identity_pool,
        workload_identity_provider,
        workload_identity_service_account)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in github_actions_config
        elif not is_included:
            assert snippet not in github_actions_config
