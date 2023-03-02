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

import os
import subprocess
import yaml

from AutoMLOps import BuilderUtils

LEFT_BRACKET = '{'
RIGHT_BRACKET = '}'

def formalize(top_lvl_name: str, 
              defaults_file: str, 
              run_local: bool):
    """Constructs and writes terraform scripts: Generates infrastructure using terraform resource management style.

    Args:
        top_lvl_name: Top directory name.
        defaults_file: Path to the default config variables yaml.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(defaults_file)
    
    BuilderUtils.make_dirs([top_lvl_name + 'terraform'])
    
    terraform_folder = top_lvl_name + 'terraform/'
    run_sh = terraform_folder + 'run_terraform.sh'
    
    BuilderUtils.write_and_chmod(terraform_folder + 'main.tf', _create_main(run_local))
    BuilderUtils.write_and_chmod(terraform_folder + 'versions.tf', _create_versions())
    BuilderUtils.write_and_chmod(terraform_folder + 'iam.tf', _create_iam())
    BuilderUtils.write_and_chmod(terraform_folder + 'variables.tf', _create_variables(defaults, run_local))
    BuilderUtils.write_and_chmod(terraform_folder + 'variables.auto.tfvars', _create_variable_vals(defaults, run_local))
    BuilderUtils.write_and_chmod(run_sh, _create_runner_script(defaults))
    

def _create_main(run_local: bool):
    """Generates code for main.tf, the terraform script that creates the primary resources.

    Args:
        run_local: Flag that determines whether to use Cloud Run CI/CD.

    Returns:
        str: Main terraform script.
    """
    main = (
        BuilderUtils.LICENSE +
        f'# Enable Google Cloud APIs\n'
        f'module "google_project_service" {LEFT_BRACKET}\n'
        f'  source                  = "terraform-google-modules/project-factory/google//modules/project_services"\n'
        f'  version                 = "14.1.0"\n'
        f'  project_id              = var.project_id\n'
        f'  activate_apis           = [\n'
        f'    "aiplatform.googleapis.com",\n'
        f'    "artifactregistry.googleapis.com",\n'
        f'    "cloudbuild.googleapis.com",\n'
        f'    "cloudresourcemanager.googleapis.com",\n'
        f'    "cloudscheduler.googleapis.com",\n'
        f'    "cloudtasks.googleapis.com",\n'
        f'    "compute.googleapis.com",\n'
        f'    "iam.googleapis.com",\n'
        f'    "iamcredentials.googleapis.com",\n'
        f'    "ml.googleapis.com",\n'
        f'    "run.googleapis.com",\n'
        f'    "storage.googleapis.com",\n'
        f'    "sourcerepo.googleapis.com"\n'
        f'    ]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        f'# Create GCS bucket\n'
        f'resource "google_storage_bucket" "gcs_bucket" {LEFT_BRACKET}\n'
        f'  project                 = var.project_id\n'
        f'  name                    = var.gs_bucket_name\n'
        f'  location                = var.gs_bucket_location\n'
        f'  depends_on              = [module.google_project_service]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        f'# Create GCS bucket to hold state file\n'
        f'resource "google_storage_bucket" "gcs_statefile_bucket" {LEFT_BRACKET}\n'
        f'  project                 = var.project_id\n'
        f'  name                    = "${LEFT_BRACKET}var.project_id{RIGHT_BRACKET}-bucket-tfstate"\n'
        f'  location                = var.gs_bucket_location\n'
        f'  force_destroy           = false\n'
        f'  storage_class           = "STANDARD"\n'
        f'  versioning {LEFT_BRACKET}\n'
        f'    enabled               = true\n'
        f'  {RIGHT_BRACKET}\n'
        f'  depends_on              = [module.google_project_service]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        f'# Create artifact registry repository\n'
        f'resource "google_artifact_registry_repository" "af_repo" {LEFT_BRACKET}\n'
        f'  project                 = var.project_id\n'
        f'  location                = var.af_registry_location\n'
        f'  repository_id           = var.af_registry_name\n'
        f'  description             = "Artifact Registry ${LEFT_BRACKET}var.af_registry_name{RIGHT_BRACKET} in ${LEFT_BRACKET}var.af_registry_location{RIGHT_BRACKET}."\n'
        f'  format                  = "DOCKER"\n'
        f'  depends_on              = [module.google_project_service]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        f'# Create cloud source repo\n'
        f'resource "google_sourcerepo_repository" "my-repo" {LEFT_BRACKET}\n'
        f'  project                 = var.project_id\n'
        f'  name                    = var.csr_name\n'
        f'  depends_on              = [module.google_project_service]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        f'# Create cloud tasks queue\n'
        f'resource "google_cloud_tasks_queue" "my-task" {LEFT_BRACKET}\n'
        f'  project                 = var.project_id\n'
        f'  name                    = var.cloud_tasks_queue_name\n'
        f'  location                = var.cloud_tasks_queue_location\n'
        f'  depends_on              = [module.google_project_service]\n'
        f'{RIGHT_BRACKET}\n'
        f'\n'
        )
    
    if not run_local:
        main += (
            f'# Create cloud build trigger\n'
            f'resource "google_cloudbuild_trigger" "my-trigger" {LEFT_BRACKET}\n'
            f'  project                 = var.project_id\n'
            f'  name                    = var.cb_trigger_name\n'
            f'  location                = var.cb_trigger_location\n'
            f'  depends_on              = [module.google_project_service, module.cloudbuild_sa_member_roles]\n'
            f'\n'
            f'  trigger_template {LEFT_BRACKET}\n'
            f'    branch_name           = var.csr_branch_name\n'
            f'    project_id            = var.project_id\n'
            f'    repo_name             = var.csr_name\n'
            f'{RIGHT_BRACKET}\n'
            f'\n'
            f'  filename                = "AutoMLOps/cloudbuild.yaml"\n'
            f'{RIGHT_BRACKET}\n'
        )
        
    return main

def _create_versions():
    """Generates code for versions.tf, the terraform script that contains the versioning details.

    Returns:
        str: Versioning terraform script.
    """
    return (
        BuilderUtils.LICENSE +
        f'terraform {LEFT_BRACKET}\n'
        f'  required_version = ">= 0.13"\n'
        f'  required_providers {LEFT_BRACKET}\n'
        f'\n'
        f'    google = {LEFT_BRACKET}\n'
        f'      source  = "hashicorp/google"\n'
        f'      version = "~> 4.49.0"\n'
        f'    {RIGHT_BRACKET}\n'
        f'  {RIGHT_BRACKET}\n'
        f'{RIGHT_BRACKET}'
    )
    
def _create_iam():
    """Generates code for iam.tf, the terraform script that contains changes to IAM permissions.

    Returns:
        str: IAM terraform script.
    """
    return (
       BuilderUtils.LICENSE +
       f'# Create pipeline runner service account\n'
       f'resource "google_service_account" "service_account" {LEFT_BRACKET}\n'
       f'  project                 = var.project_id\n'
       f'  account_id              = var.pipeline_runner_sa\n'
       f'  display_name            = "Pipeline Runner Service Account"\n'
       f'  description             = "For submitting PipelineJobs"\n'
       f'{RIGHT_BRACKET}\n'
       f'\n' 
       f'# Add IAM roles to pipeline runner service account\n'
       f'module "pipeline_sa_member_roles" {LEFT_BRACKET}\n'
       f'  source                  = "terraform-google-modules/iam/google//modules/member_iam"\n'
       f'  version                 = "7.5.0"\n'
       f'  project_id              = var.project_id\n'
       f'  prefix                  = "serviceAccount"\n'
       f'  service_account_address = "${LEFT_BRACKET}var.pipeline_runner_sa{RIGHT_BRACKET}@${LEFT_BRACKET}var.project_id{RIGHT_BRACKET}.iam.gserviceaccount.com"\n'
       f'  depends_on              = [google_service_account.service_account]\n'
       f'  project_roles           = [\n'
       f'    "roles/aiplatform.user",\n'
       f'    "roles/artifactregistry.reader",\n'
       f'    "roles/bigquery.user",\n'
       f'    "roles/bigquery.dataEditor",\n'
       f'    "roles/iam.serviceAccountUser",\n'
       f'    "roles/storage.admin",\n'
       f'    "roles/run.admin"\n'
       f'    ]\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'# Add IAM roles to cloudbuild service account\n'
       f'module "cloudbuild_sa_member_roles" {LEFT_BRACKET}\n'
       f'  source                  = "terraform-google-modules/iam/google//modules/member_iam"\n'
       f'  version                 = "7.5.0"\n'
       f'  project_id              = var.project_id\n'
       f'  prefix                  = "serviceAccount"\n'
       f'  service_account_address = "${LEFT_BRACKET}var.project_number{RIGHT_BRACKET}@cloudbuild.gserviceaccount.com"\n'
       f'  depends_on              = [module.google_project_service]\n'
       f'  project_roles           = [\n'
       f'    "roles/run.admin",\n'
       f'    "roles/iam.serviceAccountUser",\n'
       f'    "roles/cloudtasks.enqueuer",\n'
       f'    "roles/cloudscheduler.admin"\n'
       f'    ]\n'
       f'{RIGHT_BRACKET}\n'
    )
    
def _create_variables(defaults: dict, 
                      run_local: bool):
    """Generates code for variables.tf, the terraform script that describes all variables.

    Args:
        defaults: Default config variables dictionary.
        run_local: Flag that determines whether to use Cloud Run CI/CD.

    Returns:
        str: Variables terraform script.
    """
    variables = (
       BuilderUtils.LICENSE +
       f'variable "project_id" {LEFT_BRACKET}\n'
       f'  description   = "The ID of the project in which to provision resources."\n'
       f'  type          = string\n'
       f'{RIGHT_BRACKET}\n'
       f'variable "project_number" {LEFT_BRACKET}\n'
       f'  description   = "The number of the project in which to provision resources."\n'
       f'  type          = string\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'variable "gs_bucket_name" {LEFT_BRACKET}\n'
       f'  description   = "Name of GCS bucket to create."\n'
       f'  type          = string\n'
       f'  default       = "{defaults["gcp"]["project_id"]}-bucket"\n'
       f'{RIGHT_BRACKET}\n'
       '\n'
       f'variable "gs_bucket_location" {LEFT_BRACKET}\n'
       f'  description   = "Region for GCS bucket."\n'
       f'  type          = string\n'
       f'  default       = "us-central1"\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'variable "af_registry_name" {LEFT_BRACKET}\n'
       f'  description   = "Artifact registry name."\n'
       f'  type          = string\n'
       f'  default       = "vertex-mlops-af"\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'variable "af_registry_location" {LEFT_BRACKET}\n'
       f'  description   = "Artifact registry location."\n'
       f'  type          = string\n'
       f'  default       = "us-central1"\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'variable "pipeline_runner_sa" {LEFT_BRACKET}\n'
       f'  description   = "Name of service account"\n'
       f'  type          = string\n'
       f'  default       = "vertex-pipelines"\n'
       f'{RIGHT_BRACKET}\n'
       f'\n'
       f'variable "cloud_tasks_queue_name" {LEFT_BRACKET}\n'
       f'  description   = "Name of cloud tasks queue"\n'
       f'  type          = string\n'
       f'  default       = "queueing-svc"\n'
       f'{RIGHT_BRACKET}\n'
       f'variable "cloud_tasks_queue_location" {LEFT_BRACKET}\n'
       f'  description   = "Cloud tasks queue location"\n'
       f'  type          = string\n'
       f'  default       = "us-central1"\n'
       f'{RIGHT_BRACKET}\n'
    )
    
    if not run_local:
        variables += (
            f'\n'
            f'variable "cb_trigger_name" {LEFT_BRACKET}\n'
            f'  description   = "The name of cloud build trigger."\n'
            f'  type          = string\n'
            f'  default       = "automlops-trigger"\n'
            f'{RIGHT_BRACKET}\n'
            f'\n'
            f'variable "cb_trigger_location" {LEFT_BRACKET}\n'
            f'  description   = "The location of the cloudbuild trigger"\n'
            f'  type          = string\n'
            f'  default       = "us-central1"\n'
            f'{RIGHT_BRACKET}\n' 
            f'\n'
            f'variable "csr_branch_name" {LEFT_BRACKET}\n'
            f'  description   = "Name of the cloud source repository branch."\n'
            f'  type          = string\n'
            f'  default   = "automlops"\n'
            f'{RIGHT_BRACKET}\n'
            f'\n'
            f'variable "csr_name" {LEFT_BRACKET}\n'
            f'  description   = "Original source CSR"\n'
            f'  type          = string\n'
            f'  default       = "AutoMLOps-repo"\n'
            f'{RIGHT_BRACKET}'
        )
    
    return variables

def _create_variable_vals(defaults: dict, 
                          run_local: bool):
    """Generates code for variables.auto.tfvars, the terraform script that contains the values of all variables.

    Args:
        defaults: Default config variables dictionary.
        run_local: Flag that determines whether to use Cloud Run CI/CD.

    Returns:
        str: Variable values terraform script.
    """
    # Find executing account
    acct = subprocess.check_output('gcloud config list account --format "value(core.account)"', shell=True, text=True, stderr=subprocess.STDOUT).replace('\n', '')
    acct_type = "user" if "gserviceaccount" in acct else "serviceAccount"
    
    variable_vals = (
        BuilderUtils.LICENSE +
        f'''project_id                  = "{defaults['gcp']['project_id']}"\n\n'''
        f'''project_number              = "{defaults['gcp']['project_number']}"\n\n'''
        f'''gs_bucket_name              = "{defaults['gcp']['gs_bucket_name']}"\n\n'''
        f'''gs_bucket_location          = "{defaults['pipelines']['pipeline_region']}"\n\n'''
        f'''af_registry_name            = "{defaults['gcp']['af_registry_name']}"\n\n'''
        f'''af_registry_location        = "{defaults['gcp']['af_registry_location']}"\n\n'''
        f'''cloud_tasks_queue_name      = "{defaults['gcp']['cloud_tasks_queue_name']}"\n\n'''
        f'''cloud_tasks_queue_location  = "{defaults['gcp']['cloud_tasks_queue_location']}"\n\n'''
    )
    
    if not run_local:
                
        variable_vals += (
            f'''cb_trigger_name             = "{defaults['gcp']['cb_trigger_name']}"\n\n'''
            f'''cb_trigger_location         = "{defaults['gcp']['cb_trigger_location']}"\n\n'''
            f'''csr_name                    = "{defaults['gcp']['cloud_source_repository']}"\n\n'''
            f'''csr_branch_name             = "{defaults['gcp']['cloud_source_repository_branch']}"\n\n'''
        )
    
    return variable_vals

def _create_runner_script(defaults):
    """Generates code for run_terraform.sh, the runner shell script for the terraform module.

    Returns:
        str: Terraform runner script.
    """
    return (
        f'''#!/bin/bash\n'''
        + BuilderUtils.LICENSE +
        f'''# Submit initial terraform run creating all resources\n'''
        f'''terraform init\n'''
        f'''terraform validate\n'''
        f'''terraform apply -auto-approve\n'''
        f'''\n'''
        f'''# Create backend.tf to copy the state file to the newly created bucket\n'''
        f'''touch backend.tf\n'''
        f'''cat <<EOF >backend.tf\n'''
        f'''terraform {LEFT_BRACKET}\n'''
        f'''  backend "gcs" {LEFT_BRACKET}\n'''
        f'''    bucket = "{defaults['gcp']['project_id']}-bucket-tfstate"\n'''
        f'''    prefix = "terraform/state"\n'''
        f'''  {RIGHT_BRACKET}\n'''
        f'''{RIGHT_BRACKET}\n'''
        f'''EOF\n'''
        f'''\n'''
        f'''# Submit terraform run to copy the state file to the cloud bucket'''
        f'''terraform init -force-copy\n'''
        f'''terraform validate\n'''
        f'''terraform apply -auto-approve\n'''
    )
