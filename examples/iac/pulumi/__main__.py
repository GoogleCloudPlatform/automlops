# -*- coding: utf-8 -*-

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

import pulumi_gcp as gcp

from pulumi import Config, log, ResourceOptions, export


config = Config()

#######################################################################
# General Config
#######################################################################
general_cfg = config.require_object("general")

project_name = general_cfg["project_name"]
environment = general_cfg.get("environment")
default_region = general_cfg.get("default_region")

stack_infra = f"{project_name}-{environment}"

common_labels = {
    "stack": stack_infra,
    "environment": environment,
}

#######################################################################
# Project Config
#######################################################################
project_cfg = config.require_object("project")

child_folder = project_cfg.get("child_folder")
billing_account = project_cfg.get("billing_account")
disable_dependent_services = project_cfg.get("disable_dependent_services")
enable_apis = project_cfg.get("enable_apis") or []

#######################################################################
# Container Registry Config
#######################################################################
registrie = config.require_object("container_registry")

registrie_location = registrie.get("location")

#######################################################################
# Init
#######################################################################
try:
    project_init = gcp.organizations.Project(
        resource_name=stack_infra,
        name=stack_infra,
        project_id=stack_infra,
        folder_id=child_folder,
        billing_account=billing_account,
        auto_create_network=True,
        labels=common_labels,
        opts=ResourceOptions(
            providers=None,
            protect=True,
            depends_on=[]
        )
    )

    for i, service in enumerate(enable_apis):
        gcp.projects.Service(
            resource_name=f"{stack_infra}-serviceapi-{i}",
            project=project_init.project_id,
            service=service,
            disable_dependent_services=disable_dependent_services,
            opts=ResourceOptions(
                providers=None,
                protect=False,
                depends_on=[
                    project_init
                ]
            )
        )

    registry_init = gcp.container.Registry(
        resource_name=f"{stack_infra}-registry",
        project=project_init.project_id,
        location=registrie_location,
        opts=ResourceOptions(
            providers=None,
            protect=False,
            depends_on=[
                project_init
            ]
        )
    )

    export("project", project_init)

#######################################################################
except Exception as ex:
    log.error(f"Environment {environment} -> {ex}")
    raise ex
#######################################################################
