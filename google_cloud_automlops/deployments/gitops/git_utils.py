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

"""Utility functions and globals to be used by all
   other modules in this directory."""

# pylint: disable=C0103
# pylint: disable=line-too-long

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

import logging
import os
import subprocess

from jinja2 import Template

from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_DEFAULTS_FILE,
    GITOPS_TEMPLATES_PATH
)

from google_cloud_automlops.utils.utils import (
    execute_process,
    read_yaml_file,
    write_file
)
from google_cloud_automlops.deployments.enums import (
    CodeRepository,
    Deployer
)

def git_workflow():
    """Initializes a git repo if one doesn't already exist,
       then pushes to the specified branch and triggers a build job.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    deployment_framework = defaults['tooling']['deployment_framework']
    source_repository_type = defaults['gcp']['source_repository_type']
    if source_repository_type == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
        git_remote_origin_url = f'''https://source.developers.google.com/p/{defaults['gcp']['project_id']}/r/{defaults['gcp']['source_repository_name']}'''
    elif source_repository_type == CodeRepository.GITHUB.value:
        git_remote_origin_url = f'''git@github.com:{defaults['gcp']['source_repository_name']}.git'''
    elif source_repository_type == CodeRepository.GITLAB.value:
        git_remote_origin_url = f'''git@gitlab.com:{defaults['gcp']['source_repository_name']}.git'''
    elif source_repository_type == CodeRepository.BITBUCKET.value:
        git_remote_origin_url = f'''git@bitbucket.org:{defaults['gcp']['source_repository_name']}.git'''

    if not os.path.exists('.git'):
        # Initialize git and configure credentials
        execute_process('git init', to_null=False)
        if source_repository_type == CodeRepository.CLOUD_SOURCE_REPOSITORIES.value:
            execute_process(
                '''git config --global credential.'https://source.developers.google.com'.helper gcloud.sh''', to_null=False)
        # Add repo and branch
        execute_process(
            f'''git remote add origin {git_remote_origin_url}''', to_null=False)
        execute_process(
            f'''git checkout -B {defaults['gcp']['source_repository_branch']}''', to_null=False)
        has_remote_branch = subprocess.check_output(
            [f'''git ls-remote origin {defaults['gcp']['source_repository_branch']}'''], shell=True, stderr=subprocess.STDOUT)

        # This will initialize the branch, a second push will be required to trigger the cloudbuild job after initializing
        if not has_remote_branch:
            write_file('.gitignore', _create_gitignore_jinja(), 'w')
            execute_process('git add .gitignore', to_null=False)
            execute_process('''git commit -m 'init' ''', to_null=False)
            execute_process(
                f'''git push origin {defaults['gcp']['source_repository_branch']} --force''', to_null=False)

    # Check for remote origin url mismatch
    actual_remote = subprocess.check_output(
        ['git config --get remote.origin.url'], shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')
    if actual_remote != git_remote_origin_url:
        raise RuntimeError(
            f'Expected remote origin url {git_remote_origin_url} but found {actual_remote}. Reset your remote origin url to continue.')

    # Add, commit, and push changes to CSR
    execute_process(f'git add {BASE_DIR} ', to_null=False)
    # Gitlab CI and Github Actions are roadmap items
    # if deployment_framework == Deployer.GITHUB_ACTIONS.value:
    #     execute_process('git add .github/workflows/.github-ci.yml ', to_null=False)
    # elif deployment_framework == Deployer.GITLAB_CI.value:
    #     execute_process('git add .gitlab-ci.yml ', to_null=False)
    execute_process('''git commit -m 'Run AutoMLOps' ''', to_null=False)
    execute_process(
        f'''git push origin {defaults['gcp']['source_repository_branch']} --force''', to_null=False)
    # pylint: disable=logging-fstring-interpolation
    logging.info(
        f'''Pushing code to {defaults['gcp']['source_repository_branch']} branch, triggering build...''')
    if deployment_framework == Deployer.CLOUDBUILD.value:
        logging.info(
            f'''Cloud Build job running at: https://console.cloud.google.com/cloud-build/builds;region={defaults['gcp']['build_trigger_location']}''')


def _create_gitignore_jinja() -> str:
    """Generates code for .gitignore file.

    Returns:
        str: .gitignore file.
    """
    template_file = import_files(GITOPS_TEMPLATES_PATH) / 'gitignore.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render()
