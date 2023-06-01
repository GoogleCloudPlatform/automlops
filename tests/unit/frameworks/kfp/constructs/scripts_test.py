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

import os
import pytest
import yaml
from contextlib import nullcontext as does_not_raise
import pandas as pd
from AutoMLOps.frameworks.kfp.constructs.scripts import KfpScripts 

# @pytest.mark.skip
def test_init():
    """Tests the initialization of the KFPScripts class."""
    kfp_scripts = KfpScripts(
        af_registry_location="us-central1",
        af_registry_name="my-registry",
        cb_trigger_location="us-central1",
        cb_trigger_name="my-trigger",
        cloud_run_location="us-central1",
        cloud_run_name="my-run",
        cloud_tasks_queue_location="us-central1",
        cloud_tasks_queue_name="my-queue",
        csr_branch_name="main",
        csr_name="my-repo",
        default_image="gcr.io/my-project/my-image",
        gs_bucket_location="us-central1",
        gs_bucket_name="my-bucket",
        pipeline_runner_sa="my-service-account",
        project_id="my-project",
        run_local=False,
        schedule_location="us-central1",
        schedule_name="my-schedule",
        schedule_pattern="0 12 * * *",
        base_dir="base_dir",
        vpc_connector="my-connector",
    )

    assert kfp_scripts.__af_registry_location == "us-central1"
    assert kfp_scripts.__af_registry_name == "my-registry"
    assert kfp_scripts.__cb_trigger_location == "us-central1"
    assert kfp_scripts.__cb_trigger_name == "my-trigger"
    assert kfp_scripts.__cloud_run_location == "us-central1"
    assert kfp_scripts.__cloud_run_name == "my-run"
    assert kfp_scripts.__cloud_tasks_queue_location == "us-central1"
    assert kfp_scripts.__cloud_tasks_queue_name == "my-queue"
    assert kfp_scripts.__cloud_source_repository_branch == "main"
    assert kfp_scripts.__cloud_source_repository == "my-repo"
    assert kfp_scripts.__default_image == "gcr.io/my-project/my-image"
    assert kfp_scripts.__gs_bucket_location == "us-central1"