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

"""Builds Terraform Files"""

# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=unused-import

from AutoMLOps.utils.utils import (
    write_file,
    make_dirs,
)

from AutoMLOps.utils.constants import (
    GENERATED_LICENSE,
    RIGHT_BRACKET,
    LEFT_BRACKET,
    NEWLINE,
)

from AutoMLOps.iac.configs import TerraformConfig


def builder(
    project_id: str,
    config: TerraformConfig,
):
    """Constructs and writes terraform scripts: Generates infrastructure using terraform hcl resource management style.

    Args:
        project_id: The project ID.
        provider: The provider option (default: Provider.TERRAFORM).
        config.pipeline_model_name: Name of the model being deployed.
        config.creds_tf_var_name: Name of tf variable with project access credentials json key 
        config.region: region used in gcs infrastructure config.
        config.gcs_bucket_name: gcs bucket name to use as part of the model infrastructure
        config.artifact_repo_name: name of the artifact registry for the model infrastructure
        config.source_repo_name: source repository used as part of the the model infra
        config.cloudtasks_queue_name: name of the task queue used for model scheduling
        config.cloud_build_trigger_name: name of the cloud build trigger for the model infra
        config.workspace_name: Name of the terraform cloud workspace.
    """

    # Define the model name for the IaC configurations
    # remove special characters and spaces
    pipeline_model_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.pipeline_model_name]).lower()

    creds_tf_var_name = ''.join(
        ['_' if c in ['.', '-', '/', ' '] else c for c in config.creds_tf_var_name]).upper()

    workspace_name = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in config.workspace_name]).lower()

    project_id = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in project_id]).lower()

    gcs_bucket_name = ''.join(
        ['_' if c in ['.', '/', ' '] else c for c in config.gcs_bucket_name]).lower()
    
    artifact_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.artifact_repo_name]).lower()
    
    source_repo_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.source_repo_name]).lower()

    cloudtasks_queue_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloudtasks_queue_name]).lower()

    cloud_build_trigger_name = ''.join(
        ['-' if c in ['.', '_', '/', ' '] else c for c in config.cloud_build_trigger_name]).lower()

    # create terraform folder
    make_dirs([pipeline_model_name + '/'])
    terraform_folder = pipeline_model_name + '/'

    # create variables.tf
    write_file(terraform_folder + 'variables.tf', _create_variables_tf(
        creds_tf_var_name=creds_tf_var_name,), 'w+')
    
    # create terraform.tfvars
    write_file(terraform_folder + 'terraform.tfvars', _create_terraform_tfvars(
        creds_tf_var_name=creds_tf_var_name,), 'w+')

    # create provider.tf
    write_file(terraform_folder + 'provider.tf', _create_provider_tf(
        creds_tf_var_name=creds_tf_var_name,), 'w+')
    
    # create outputs.tf
    write_file(terraform_folder + 'outputs.tf', _create_outputs_tf(), 'w+')

    # create data.tf
    write_file(terraform_folder + 'data.tf', _create_data_tf(
        workspace_name=workspace_name,
        project_id=project_id,
        pipeline_model_name=pipeline_model_name,
        region=config.region), 'w+')
    
    # create main.tf
    write_file(terraform_folder + 'main.tf', _create_main_tf(
        pipeline_model_name=pipeline_model_name,
        region=config.region,
        gcs_bucket_name=gcs_bucket_name,
        artifact_repo_name=artifact_repo_name,
        source_repo_name=source_repo_name,
        cloudtasks_queue_name=cloudtasks_queue_name,
        cloud_build_trigger_name=cloud_build_trigger_name,), 'w+')
    
    # create iam.tf
    write_file(terraform_folder + 'iam.tf', _create_iam_tf(), 'w+')
    

def _create_variables_tf(
        creds_tf_var_name: str,
) -> str:
    """Generates code for variables.tf, the terraform hcl script that contains variables used to deploy project's environment.

    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: variables.tf config script.
    """

    return (
        f'variable \"{creds_tf_var_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'  description   = \"Credentials json key to access google project\"{NEWLINE}'
        f'  type          = string{NEWLINE}'
        f'  default       = \"\"{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'variable \"pipeline_runner_sa\" {LEFT_BRACKET}{NEWLINE}'
        f'  description   = \"Name of pipeline runner service account\"{NEWLINE}'
        f'  type          = string{NEWLINE}'
        f'  default       = \"pipeline-runner-sa\"{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'variable \"cloudbuild_runner_sa\" {LEFT_BRACKET}{NEWLINE}'
        f'  description   = \"Name of cloud build runner service account\"{NEWLINE}'
        f'  type          = string{NEWLINE}'
        f'  default       = \"cloudbuild-runner-sa\"{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_terraform_tfvars(
        creds_tf_var_name: str,
) -> str:
    """Generates code for terraform.tfvars, the terraform hcl script that contains teraform variables used to deploy project's environment.
    
    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: terraform.tfvars config script.
    """

    return (
        f'{creds_tf_var_name} = \"\"{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_provider_tf(
        creds_tf_var_name: str,
) -> str:
    """Generates code for provider.tf, the terraform hcl script that contains teraform providers used to deploy project's environment.

    Args:
        creds_tf_var_name: Name of tf variable with project access credentials json key.

    Returns:
        str: provider.tf config script.
    """

    return (
        f'provider \"google\" {LEFT_BRACKET}{NEWLINE}'
        f'  credentials = var.{creds_tf_var_name}{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'provider \"google-beta\" {LEFT_BRACKET}{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_outputs_tf() -> str:
    """Generates code for outputs.tf, the terraform hcl script that contains outputs from project's environment.
    Args:
        takes no arguments.

    Returns:
        str: outputs.tf config script.
    """

    return (
        f'output \"apis\" {LEFT_BRACKET}{NEWLINE}'
        f'  value = local.org_project.enable_apis{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_data_tf(
    workspace_name: str,
    project_id: str,
    region: str,
    pipeline_model_name: str,
) -> str:
    """Generates code for data.tf, the terraform hcl script that contains terraform remote backend and org project details.

    Args:
        workspace_name: Name of the terraform cloud workspace.
        project_id: The project ID.
        region: region used in gcs infrastructure config.
        pipeline_model_name: Name of the model being deployed.

    Returns:
        str: data.tf config script.
    """

    return (
        f'terraform {LEFT_BRACKET}{NEWLINE}'
        f'  backend \"remote\" {LEFT_BRACKET}{NEWLINE}'
        f'    organization = \"***\" ## provided by customer{NEWLINE}'
        f'    workspaces {LEFT_BRACKET}{NEWLINE}'
        f'      name = \"{workspace_name}\" ## provided by customer{NEWLINE}'
        f'    {RIGHT_BRACKET}{NEWLINE}'
        f'  {RIGHT_BRACKET}{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'/******************************************{NEWLINE}'
        f'  Locals{NEWLINE}'
        f'*****************************************/{NEWLINE}'
        f'locals {LEFT_BRACKET}{NEWLINE}'
        f'  project_id        = \"{project_id}\"'
        f'{NEWLINE}'
        f'  naming_convention = {LEFT_BRACKET}{NEWLINE}'
        f'    platform_name   = \"gcp-automlops\"{NEWLINE}'
        f'    app             = \"{pipeline_model_name}\"{NEWLINE}'
        f'  {RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'  org_project = {LEFT_BRACKET}{NEWLINE}'
        f'    billing_account = \"***\"{NEWLINE}'
        f'    folder          = \"folders/***\"{NEWLINE}'
        f'    region          = \"{region}\"{NEWLINE}'
        f'{NEWLINE}'
        f'    enable_apis = [{NEWLINE}'
        f'      \"aiplatform.googleapis.com\",{NEWLINE}'
        f'      \"artifactregistry.googleapis.com\",{NEWLINE}'
        f'      \"cloudbuild.googleapis.com\",{NEWLINE}'
        f'      \"cloudresourcemanager.googleapis.com\",{NEWLINE}'
        f'      \"cloudscheduler.googleapis.com\",{NEWLINE}'
        f'      \"cloudtasks.googleapis.com\",{NEWLINE}'
        f'      \"compute.googleapis.com\",{NEWLINE}'
        f'      \"iam.googleapis.com\",{NEWLINE}'
        f'      \"iamcredentials.googleapis.com\",{NEWLINE}'
        f'      \"ml.googleapis.com\",{NEWLINE}'
        f'      \"run.googleapis.com\",{NEWLINE}'
        f'      \"storage.googleapis.com\",{NEWLINE}'
        f'      \"sourcerepo.googleapis.com\",{NEWLINE}'
        f'      \"bigquery.googleapis.com\",{NEWLINE}'
        f'      \"logging.googleapis.com\",{NEWLINE}'
        f'      \"monitoring.googleapis.com\",{NEWLINE}'
        f'      \"pubsub.googleapis.com\",{NEWLINE}'
        f'      \"secretmanager.googleapis.com\",{NEWLINE}'
        f'      \"dataflow.googleapis.com\",{NEWLINE}'
        f'      \"datacatalog.googleapis.com\",{NEWLINE}'
        f'      \"composer.googleapis.com\",{NEWLINE}'
        f'      \"dataform.googleapis.com\",{NEWLINE}'
        f'      \"retail.googleapis.com\",{NEWLINE}'
        f'      \"recommendationengine.googleapis.com\",{NEWLINE}'
        f'      \"notebooks.googleapis.com\",{NEWLINE}'
        f'      \"storage-component.googleapis.com\",{NEWLINE}'
        f'      \"visionai.googleapis.com\",{NEWLINE}'
        f'    ]{NEWLINE}'
        f'  {RIGHT_BRACKET}{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_main_tf(
    pipeline_model_name: str,
    region: str,
    gcs_bucket_name: str,
    artifact_repo_name: str,
    source_repo_name: str,
    cloudtasks_queue_name,
    cloud_build_trigger_name,
) -> str:
    """Generates code for main.tf, the terraform hcl script that contains terraform resources configs to deploy resources in the gcs project.

    Args:
        pipeline_model_name: Name of the model being deployed.
        region: region used in gcs infrastructure config.
        gcs_bucket_name: gcs bucket name to use as part of the model infrastructure
        artifact_repo_name: name of the artifact registry for the model infrastructure
        source_repo_name: source repository used as part of the the model infra
        cloudtasks_queue_name: name of the task queue used for model scheduling
        cloud_build_trigger_name: name of the cloud build trigger for the model infra
        
    Returns:
        str: main.tf config script.
    """

    return (
        f'module \"{pipeline_model_name}_{gcs_bucket_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'  source     = \"terraform-google-modules/cloud-storage/google\"{NEWLINE}'
        f'  version    = \"~> 3.4\"{NEWLINE}'
        f'  project_id = local.project_id{NEWLINE}'
        f'  prefix     = local.project_id{NEWLINE}'
        f'  location   = \"US\"{NEWLINE}'
        f'  names      = [\"{gcs_bucket_name}\"]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'

        f'resource \"google_service_account\" \"pipeline_service_account\" {LEFT_BRACKET}{NEWLINE}'
        f'  project      = local.project_id{NEWLINE}'
        f'  display_name = \"Pipeline Runner Service Account\"{NEWLINE}'
        f'  account_id   = var.pipeline_runner_sa{NEWLINE}'
        f'  description  = \"For submitting PipelineJobs\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = []{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_service_account\" \"cloudbuild_service_account\" {LEFT_BRACKET}{NEWLINE}'
        f'  project      = local.project_id{NEWLINE}'
        f'  display_name = \"Cloud Build Runner Service Account\"{NEWLINE}'
        f'  account_id   = var.cloudbuild_runner_sa{NEWLINE}'
        f'  description  = \"For submitting Cloud Build Jobs\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = []{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_artifact_registry_repository\" \"{pipeline_model_name}_{artifact_repo_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'  project       = local.project_id{NEWLINE}'
        f'  location      = \"{region}\"{NEWLINE}'
        f'  repository_id = \"{artifact_repo_name}\"{NEWLINE}'
        f'  description   = \"Docker artifact repository\"{NEWLINE}'
        f'  format        = \"DOCKER\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = []{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_sourcerepo_repository\" \"{pipeline_model_name}_{source_repo_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'project = local.project_id{NEWLINE}'
        f'name    = \"{source_repo_name}\"{NEWLINE}'
        f'{NEWLINE}'
        f'depends_on = []{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_cloud_tasks_queue\" \"{pipeline_model_name}_{cloudtasks_queue_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'  project    = local.project_id{NEWLINE}'
        f'  name       = \"{cloudtasks_queue_name}\"{NEWLINE}'
        f'  location   = \"{region}\"{NEWLINE}'
        f'  depends_on = []{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'resource \"google_cloudbuild_trigger\" \"{pipeline_model_name}_{cloud_build_trigger_name}\" {LEFT_BRACKET}{NEWLINE}'
        f'  project         = local.project_id{NEWLINE}'
        f'  name            = \"{cloud_build_trigger_name}\"{NEWLINE}'
        f'  location        = \"{region}\"{NEWLINE}'
        f'  service_account = google_service_account.cloudbuild_service_account.id{NEWLINE}'
        f'{NEWLINE}'
        f'  trigger_template {LEFT_BRACKET}{NEWLINE}'
        f'    branch_name = \"main\"{NEWLINE}'
        f'    project_id  = local.project_id{NEWLINE}'
        f'    repo_name   = google_sourcerepo_repository.{pipeline_model_name}_{source_repo_name}.name{NEWLINE}'
        f'  {RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'  filename   = \"cloudbuild.yaml\"{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.cloudbuild_service_account,{NEWLINE}'
        f'    google_project_iam_member.cloudbuild_sa_run_admin,{NEWLINE}'
        f'    google_project_iam_member.cloudbuild_sa_srvs_acc_user,{NEWLINE}'
        f'    google_project_iam_member.cloudbuild_sa_cloudtasks_enq,{NEWLINE}'
        f'    google_project_iam_member.cloudbuild_sa_cloudsched_admin{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )

def _create_iam_tf() -> str:
    """Generates code for iam.tf, the terraform hcl script that contains service accounts iam bindings for project's environment.

    Args:
        takes no arguments.

    Returns:
        str: iam.tf config script.
    """

    return (
        f'##################################################################################{NEWLINE}'
        f'## IAMMember - Pipeline Runner Service Account{NEWLINE}'
        f'##################################################################################{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_aiplatform_user\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/aiplatform.user\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_artifactregistry_reader\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/artifactregistry.reader\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_bigquery_user\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/bigquery.user\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_bigquery_data_editor\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/bigquery.dataEditor\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_srvs_acc_user\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/iam.serviceAccountUser\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_storage_admin\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/storage.admin\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"pipeline_sa_run_admin\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/run.admin\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.pipeline_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.pipeline_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'##################################################################################{NEWLINE}'
        f'## IAMMember - Cloud Build Runner Service Account{NEWLINE}'
        f'##################################################################################{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"cloudbuild_sa_run_admin\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/run.admin\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.cloudbuild_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.cloudbuild_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"cloudbuild_sa_srvs_acc_user\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/iam.serviceAccountUser\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.cloudbuild_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.cloudbuild_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"cloudbuild_sa_cloudtasks_enq\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/cloudtasks.enqueuer\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.cloudbuild_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.cloudbuild_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
        f'resource \"google_project_iam_member\" \"cloudbuild_sa_cloudsched_admin\" {LEFT_BRACKET}{NEWLINE}'
        f'  project = local.project_id{NEWLINE}'
        f'  role    = \"roles/cloudscheduler.admin\"{NEWLINE}'
        f'  member  = \"serviceAccount:${LEFT_BRACKET}google_service_account.cloudbuild_service_account.email{RIGHT_BRACKET}\"{NEWLINE}'
        f'{NEWLINE}'
        f'  depends_on = [{NEWLINE}'
        f'    google_service_account.cloudbuild_service_account{NEWLINE}'
        f'  ]{NEWLINE}'
        f'{RIGHT_BRACKET}{NEWLINE}'
        f'{NEWLINE}'
    )