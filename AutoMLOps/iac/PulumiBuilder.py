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

"""Builds Pulumi Files"""

from AutoMLOps import BuilderUtils

def formalize(top_lvl_name: str,
              defaults_file: str,
              run_local: bool):
    """Constructs and writes pulumi scripts: Generates infrastructure using pulumi resource management style.

    Args:
        top_lvl_name: Top directory name.
        defaults_file: Path to the default config variables yaml.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
    """
    defaults = BuilderUtils.read_yaml_file(defaults_file)

    BuilderUtils.make_dirs([top_lvl_name + 'pulumi',
                            top_lvl_name + 'pulumi/environment'])

    pulumi_folder = top_lvl_name + 'pulumi/environment/'

    BuilderUtils.write_file(pulumi_folder + 'Pulumi.yaml', _create_versions(), 'w+')
    BuilderUtils.write_file(pulumi_folder + 'Pulumi.dev.yaml', _create_iam(), 'w+')
    BuilderUtils.write_file(pulumi_folder + 'Pulumi.prd.yaml', _create_variables(run_local), 'w+')
    BuilderUtils.write_file(pulumi_folder + '__main__.py', _create_main(run_local), 'w+')
    # follow up with stack init config

    def _create_pulumi_yaml():
        """Generates code for Pulumi.yaml, the pulumi script that contains details to deploy project's GCP environment.

        Returns:
            str: Pulumi.yaml config script.
        """
        return(
            BuilderUtils.LICENSE +
            f'name: devops_plm_environment_name_integration_name'\n
            f'runtime:'\n
            f'name: python'\n
            f'description: A Pulumi program which use the devops_plm_gcp_infra package to deploy Datalake Bronze project GCP environments'\n
        )
    
    def _create_pulumi_dev_yaml():
        """Generates code for Pulumi.dev.yaml, the pulumi script that contains details to deploy dev environment config.

        Returns:
            str: Pulumi.dev.yaml config script.
        """
        return(
            BuilderUtils.LICENSE +
            f'config:'\n
            f'    devops_plm_env_bronze_datalake_amazon:general:'\n
            f'        business_unit: dl'\n
            f'        initiative: datalake'\n
            f'        platform: bronze'\n
            f'        environment: dev'\n
            f'        default_region: us-east1'\n
            f'    devops_plm_env_bronze_datalake_amazon:buckets:'\n
            f'        - name: amazon-data-inbound'\n
            f'        location: us'\n
            f'        labels:'\n
            f'            provider: amazon'\n
            f'    devops_plm_env_bronze_datalake_mcp:service_accounts:'\n
            f'        - account_id: pipeline_runner_sa'\n
            f'        description: For submitting PipelineJobs'\n
            f'        display_name: Pipeline Runner Service Account'\n
            f'        role_bindings:'\n
            f'            - roles/aiplatform.user'\n
            f'            - roles/artifactregistry.reader'\n
            f'            - roles/bigquery.user'\n
            f'            - roles/bigquery.dataEditor'\n
            f'            - roles/iam.serviceAccountUser'\n
            f'            - roles/storage.admin'\n
            f'            - roles/run.admin'\n
            f'        - account_id: cloudbuild_runner_sa'\n
            f'        description: For submitting Cloud Build Jobs'\n
            f'        display_name: Cloud Build Runner Service Account'\n
            f'        role_bindings:'\n
            f'            - roles/run.admin'\n
            f'            - roles/iam.serviceAccountUser'\n
            f'            - roles/cloudtasks.enqueuer'\n
            f'            - roles/cloudscheduler.admin'\n
        )
    
    def _create_pulumi_prd_yaml():
        """Generates code for Pulumi.prd.yaml, the pulumi script that contains details to deploy prd environment config.

        Returns:
            str: Pulumi.prd.yaml config script.
        """
        return(
            BuilderUtils.LICENSE +
            f'config:'\n
            f'    devops_plm_env_bronze_datalake_amazon:general:'\n
            f'        business_unit: dl'\n
            f'        initiative: datalake'\n
            f'        platform: bronze'\n
            f'        environment: prd'\n
            f'        default_region: us-east1'\n
            f'    devops_plm_env_bronze_datalake_amazon:buckets:'\n
            f'        - name: amazon-data-inbound'\n
            f'        location: us'\n
            f'        labels:'\n
            f'            provider: amazon'\n
        )
    
    def _create_main(run_local: bool):
        """Generates code for __main__.py, the pulumi script that creates the primary resources.

        Args:
            run_local: Flag that determines whether to use Cloud Run CI/CD.

        Returns:
            str: Main pulumi script.
        """
        main = (
            BuilderUtils.LICENSE +
            f'import os'\n
            f'import pulumi'\n
            f'import pulumi_gcp as gcp'\n
            f'from pulumi_gcp.storage import BucketObjectArgs'\n
            f'from pulumi import Config, log, ResourceOptions, StackReference, export'\n
            f'from devops_plm_gcp_infra.storage.alpha import Bucket'\n
            f'from devops_plm_gcp_infra.iam.alpha import ServiceAccount'\n
            f'from pathlib import Path'\n
            f'from jinja2 import Template'\n
            f''\n
            f'config = Config()'\n

            #######################################################################################
            # General Config
            #######################################################################################
            general_cfg = config.require_object("general")

            business_unit = general_cfg.get("business_unit")
            initiative = general_cfg.get("initiative")
            platform = general_cfg.get("platform")
            environment = general_cfg.get("environment")
            default_region = general_cfg.get("default_region")

            integration_name = "amazon"

            stack_infra = f"{business_unit}-{initiative}-{platform}-{environment}"

            infra = StackReference(f"univision/devops_plm_env_bronze_datalake_{integration_name}/{environment}")

            project_stack_ref = pulumi.StackReference(f"univision/devops_plm_env_bronze_datalake/{environment}")

            #######################################################################################
            # Service Accounts Config
            #######################################################################################
            sas_cfg = config.require_object("service_accounts")

            sas_cfg = list(sas_cfg) if sas_cfg else []

            #######################################################################################
            # Storage Config
            #######################################################################################
            buckets = config.require_object("buckets") or []
            for bucket in buckets:
                bucket["name"] = f"{stack_infra}-{bucket.get('location')}-bkt-{bucket.get('name')}"

            #######################################################################################
            # Init
            #######################################################################################
            try:
                bucket = Bucket(
                    resource_name=stack_infra,
                    project=stack_infra,
                    buckets=buckets,
                    opts=ResourceOptions(
                        depends_on=[]
                    )
                )

                saInit = ServiceAccount(
                    resource_name=stack_infra,
                    project=stack_infra,
                    service_accounts=sas_cfg,
                    opts=ResourceOptions(
                        provider=None,
                        protect=False,
                        depends_on=[]
                    )
                )

                artifactregistry_repo = gcp.artifactregistry.Repository(
                    resource_name="my-repo",
                    project=stack_infra,
                    description="example docker repository",
                    format="DOCKER",
                    location="us-central1",
                    repository_id="my-repository",
                    opts=ResourceOptions(
                        depends_on=[]
                    )
                )

                source_repo = gcp.sourcerepo.Repository(
                    resource_name="my-repo",
                    project=stack_infra,
                    opts=ResourceOptions(
                        depends_on=[]
                    )
                )

                cloudtasks_queue = gcp.cloudtasks.Queue(
                    resource_name="cloudtasks_queue",
                    project=stack_infra,
                    location="us-central1",
                    opts=ResourceOptions(
                        depends_on=[]
                    )
                )

                filename_trigger = gcp.cloudbuild.Trigger(
                    resource_name="filename-trigger",
                    project=stack_infra,
                    filename="cloudbuild.yaml",
                    service_account=saInit.created_service_accounts[1].email
                    location="us-central1",
                    substitutions={
                    "_BAZ": "qux",
                    "_FOO": "bar",
                },
                trigger_template=gcp.cloudbuild.TriggerTriggerTemplateArgs(
                    branch_name="main",
                    repo_name="my-repo",
                ))
        )

        return main