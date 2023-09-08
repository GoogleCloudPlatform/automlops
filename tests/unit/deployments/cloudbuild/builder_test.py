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

from google_cloud_automlops.deployments.cloudbuild.builder import create_cloudbuild_jinja


@pytest.mark.parametrize(
    '''artifact_repo_location, artifact_repo_name, naming_prefix,'''
    '''project_id, pubsub_topic_name, use_ci, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-topic', True, True,
            ['id: "build_component_base"',
             'id: "push_component_base"',
             'id: "install_pipelines_deps"',
             'id: "build_pipeline_spec"',
             'id: "publish_to_topic"',
             '"build", "-t", "us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest"',
             '"push", "us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest"',
             'gcloud pubsub topics publish my-topic']
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-topic', False, True,
            ['id: "build_component_base"',
             '"build", "-t", "us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest"']
        ),
        (
            'us-central1', 'my-artifact-repo', 'my-prefix',
            'my-project', 'my-topic', False, False,
            ['id: "push_component_base"',
             'id: "install_pipelines_deps"',
             'id: "build_pipeline_spec"',
             'id: "publish_to_topic"',
             '"push" "us-central1-docker.pkg.dev/my-project/my-artifact-repo/my-prefix/components/component_base:latest"',
             'gcloud pubsub topics publish my-topic']
        ),
    ]
)
def test_create_cloudbuild_jinja(
    artifact_repo_location: str,
    artifact_repo_name: str,
    naming_prefix: str,
    project_id: str,
    pubsub_topic_name: str,
    use_ci: bool,
    is_included: bool,
    expected_output_snippets: List[str]):
    # TODO SRASTATTER - update this docstring
    """Tests the update_params function, which reformats the source code type
    """

    cloudbuild_config = create_cloudbuild_jinja(
        artifact_repo_location,
        artifact_repo_name,
        naming_prefix,
        project_id,
        pubsub_topic_name,
        use_ci)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in cloudbuild_config
        elif not is_included:
            assert snippet not in cloudbuild_config
