# List of Model integrations

cd examples/iac/terraform/

export PYTHONPATH="${HOME}/.../automlops:${PYTHONPATH}" ## modify path to the repo

python3

from AutoMLOps import AutoMLOps

from AutoMLOps.iac.enums import (Provider)

from AutoMLOps.iac.configs import TerraformConfig

terraform_config=TerraformConfig(
    pipeline_model_name="your-pipeline-model-name",
    creds_tf_var_name="your-google-credentials-tf-variable-name",
    workspace_name="your-tf-workspace-name",
    region="your-region",
    gcs_bucket_name="your-gcs-bucket-name",
    artifact_repo_name="your-artifact-repo-name",
    source_repo_name="your-source-repo-name",
    cloudtasks_queue_name="your-cloudtasks-queue-name",
    cloud_build_trigger_name="your-cloud-build-trigger-name")

AutoMLOps.iac_generate(project_id='your-project-id', provider=Provider.TERRAFORM, provider_config=terraform_config)

Move created configuration to the models folder or other desireable location.