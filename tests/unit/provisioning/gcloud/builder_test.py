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

from google_cloud_automlops.provisioning.gcloud.builder import provision_resources_script_jinja

@pytest.mark.parametrize(
    '''artifact_repo_location, artifact_repo_name, artifact_repo_type, build_trigger_location,'''
    '''build_trigger_name, deployment_framework, naming_prefix, pipeline_job_runner_service_account,'''
    '''pipeline_job_submission_service_location, pipeline_job_submission_service_name, pipeline_job_submission_service_type,'''
    '''project_id, pubsub_topic_name,'''
    '''required_apis,'''
    '''schedule_location, schedule_name, schedule_pattern,'''
    '''source_repo_branch, source_repo_name, source_repo_type, storage_bucket_location, storage_bucket_name,'''
    '''use_ci, vpc_connector, is_included,'''
    '''expected_output_snippets''',
    [
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-functions',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            True, 'my-vpc-connector', True,
            ['gcloud artifacts repositories create', 'gcloud iam service-accounts create',
             'gsutil mb -l ${STORAGE_BUCKET_LOCATION} gs://$STORAGE_BUCKET_NAME', 'gcloud iam service-accounts create',
             'gcloud projects add-iam-policy-binding', 'gcloud source repos create', 'gcloud pubsub topics create',
             'gcloud functions deploy', 'gcloud beta builds triggers create', 'gcloud scheduler jobs create pubsub',
             '--vpc-connector=my-vpc-connector']
        ),
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-run',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            True, 'No VPC Specified', True,
            ['gcloud artifacts repositories create', 'gcloud iam service-accounts create',
             'gsutil mb -l ${STORAGE_BUCKET_LOCATION} gs://$STORAGE_BUCKET_NAME', 'gcloud iam service-accounts create',
             'gcloud projects add-iam-policy-binding', 'gcloud source repos create', 'gcloud pubsub topics create',
             'gcloud builds submit ${BASE_DIR}services/submission_service', 'gcloud run deploy', 'gcloud pubsub subscriptions create',
             'gcloud beta builds triggers create', 'gcloud scheduler jobs create pubsub']
        ),
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-run',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'some-other-source-repository', 'us-central1', 'my-bucket',
            True, 'No VPC Specified', False,
            ['gcloud source repos create', 'cloud beta builds triggers create']
        ),
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-run',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', 'No Schedule Specified',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            True, 'No VPC Specified', False,
            ['gcloud scheduler jobs create pubsub', '--vpc_connector=']
        ),
        (
            'us-central1', 'my-registry', 'some-other-repo-type', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-functions',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            True, 'No VPC Specified', False,
            ['gcloud artifacts repositories create']
        ),
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'some-other-deployment-framework', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-functions',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            True, 'No VPC Specified', False,
            ['gcloud beta builds triggers create']
        ),
        (
            'us-central1', 'my-registry', 'artifact-registry', 'us-central1',
            'my-trigger', 'cloud-build', 'my-prefix', 'my-service-account@serviceaccount.com',
            'us-central1', 'my-submission-svc', 'cloud-functions',
            'my-project', 'my-topic-name',
            ['apiA','apiB','apiC'],
            'us-central1', 'my-schedule', '0 12 * * *',
            'my-branch', 'my-repo', 'cloud-source-repositories', 'us-central1', 'my-bucket',
            False, 'No VPC Specified', False,
            ['gcloud pubsub topics create', 'gcloud beta builds triggers create',
             'gcloud functions deploy', 'gcloud run deploy', 'gcloud scheduler jobs create pubsub']
        )
    ]
)
def test_provision_resources_script_jinja(
    artifact_repo_location: str,
    artifact_repo_name: str,
    artifact_repo_type: str,
    build_trigger_location: str,
    build_trigger_name: str,
    deployment_framework: str,
    naming_prefix: str,
    pipeline_job_runner_service_account: str,
    pipeline_job_submission_service_location: str,
    pipeline_job_submission_service_name: str,
    pipeline_job_submission_service_type: str,
    project_id: str,
    pubsub_topic_name: str,
    required_apis: list,
    schedule_location: str,
    schedule_name: str,
    schedule_pattern: str,
    source_repo_branch: str,
    source_repo_name: str,
    source_repo_type: str,
    storage_bucket_location: str,
    storage_bucket_name: str,
    use_ci: bool,
    vpc_connector: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests provision_resources_script_jinja, which generates code for 
       provision_resources.sh which sets up the project's environment.
       There are seven test cases for this function:
        1. Checks for relevant gcloud commands when using the following tooling:
            artifact-registry, cloud-build, cloud-functions, cloud scheduler, cloud-source-repositories, and a vpc connector
        2. Checks for relevant gcloud commands when using the following tooling:
            artifact-registry, cloud-build, cloud-run, cloud scheduler, cloud-source-repositories, and no vpc connector
        3. Checks that gcloud source repo commands are not included when not using cloud-source-repositories.
        4. Checks that gcloud scheduler command and vpc_connector flag are not included when not specifying a vpc connector or schedule.
        5. Checks that gcloud artifacts command is not included when not using artifact-registry.
        6. Checks that gcloud beta builds triggers command is not included when not using cloud-build.
        7. Checks for that CI/CD elements are not included when use_ci=False.

    Args:
        artifact_repo_location: Region of the artifact repo (default use with Artifact Registry).
        artifact_repo_name: Artifact repo name where components are stored (default use with Artifact Registry).
        artifact_repo_type: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
        build_trigger_location: The location of the build trigger (for cloud build).
        build_trigger_name: The name of the build trigger (for cloud build).
        deployment_framework: The CI tool to use (e.g. cloud build, github actions, etc.)
        naming_prefix: Unique value used to differentiate pipelines and services across AutoMLOps runs.
        pipeline_job_runner_service_account: Service Account to run PipelineJobs.
        pipeline_job_submission_service_location: The location of the cloud submission service.
        pipeline_job_submission_service_name: The name of the cloud submission service.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        project_id: The project ID.
        pubsub_topic_name: The name of the pubsub topic to publish to.
        required_apis: List of APIs that are required to run the service.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        source_repo_branch: The branch to use in the source repository.
        source_repo_name: The name of the source repository to use.
        source_repo_type: The type of source repository to use (e.g. gitlab, github, etc.)
        storage_bucket_location: Region of the GS bucket.
        storage_bucket_name: GS bucket name where pipeline run metadata is stored.
        use_ci: Flag that determines whether to use Cloud CI/CD.
        vpc_connector: The name of the vpc connector to use.
    """
    provision_resources_script = provision_resources_script_jinja(
        artifact_repo_location=artifact_repo_location,
        artifact_repo_name=artifact_repo_name,
        artifact_repo_type=artifact_repo_type,
        build_trigger_location=build_trigger_location,
        build_trigger_name=build_trigger_name,
        deployment_framework=deployment_framework,
        naming_prefix=naming_prefix,
        pipeline_job_runner_service_account=pipeline_job_runner_service_account,
        pipeline_job_submission_service_location=pipeline_job_submission_service_location,
        pipeline_job_submission_service_name=pipeline_job_submission_service_name,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        project_id=project_id,
        pubsub_topic_name=pubsub_topic_name,
        required_apis=required_apis,
        schedule_location=schedule_location,
        schedule_name=schedule_name,
        schedule_pattern=schedule_pattern,
        source_repo_branch=source_repo_branch,
        source_repo_name=source_repo_name,
        source_repo_type=source_repo_type,
        storage_bucket_location=storage_bucket_location,
        storage_bucket_name=storage_bucket_name,
        use_ci=use_ci,
        vpc_connector=vpc_connector)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in provision_resources_script
        elif not is_included:
            assert snippet not in provision_resources_script
