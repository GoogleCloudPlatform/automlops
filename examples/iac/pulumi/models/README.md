# List of Model integrations

cd examples/iac/pulumi/

export PYTHONPATH="${HOME}/.../automlops:${PYTHONPATH}" ## modify path to the repo

python3

from AutoMLOps import AutoMLOps

from AutoMLOps.iac.enums import (Provider, PulumiRuntime)

from AutoMLOps.iac.configs import PulumiConfig

pulumi_config=PulumiConfig(
    pipeline_model_name="your-pipeline-model-name",
    region="your-region",
    gcs_bucket_name="your-gcs-bucket-name",
    artifact_repo_name="your-artifact-repo-name",
    source_repo_name="your-source-repo-name",
    cloudtasks_queue_name="your-cloudtasks-queue-name",
    cloud_build_trigger_name="your-cloud-build-trigger-name",
    pulumi_runtime=PulumiRuntime.PYTHON
)

AutoMLOps.iac_generate(project_id='your-project-id', provider=Provider.PULUMI, provider_config=pulumi_config)

Move created configuration to the models folder or other desireable location.