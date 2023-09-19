# AutoMLOps

AutoMLOps is a service that generates, provisions, and deploys CI/CD integrated MLOps pipelines, bridging the gap between Data Science and DevOps. AutoMLOps provides a repeatable process that dramatically reduces the time required to build MLOps pipelines. The service generates a containerized MLOps codebase, provides infrastructure-as-code to provision and maintain the underlying MLOps infra, and provides deployment functionalities to trigger and run MLOps pipelines.

AutoMLOps gives flexibility over the tools and technologies used in the MLOps pipelines, allowing users to choose from a wide range of options for artifact repositories, build tools, provisioning tools, orchestration frameworks, and source code repositories. AutoMLOps can be configured to either use existing infra, or provision new infra, including source code repositories for versioning the generated MLOps codebase, build configs and triggers, artifact repositories for storing docker containers, storage buckets, service accounts, IAM permissions, APIs needed to run pipelines, RESTful services to allow for triggering and running pipelines asynchronous, and Cloud Scheduler jobs for triggering and running pipelines on a recurring basis.

These automatic integrations empower data scientists to take their experiments to production more quickly, allowing them to focus on what they do best: providing actionable insights through data.

# Install

Install AutoMLOps from [PyPI](https://pypi.org/project/google-cloud-automlops/): `pip install google-cloud-automlops`

Or Install locally by cloning the repo and running `pip install .`

# Dependencies
- `docopt==0.6.2`
- `docstring-parser==0.15`
- `google-api-python-client==2.97.0`
- `google-auth==2.22.0`
- `importlib-resources==6.0.1`
- `Jinja2==3.1.2`
- `packaging==23.1`
- `pipreqs==0.4.13`
- `pydantic==2.3.0`
- `PyYAML==6.0.1`
- `yarg==0.1.9`

# Usage

AutoMLOps provides 2 functions for defining MLOps pipelines:

- `@AutoMLOps.component(...)`: Defines a component, which is a containerized python function.
- `@AutoMLOps.pipeline(...)`: Defines a pipeline, which is a series of components.

AutoMLOps provides 5 functions for building and maintaining MLOps pipelines:

- `AutoMLOps.generate(...)`: Generates the MLOps codebase. Users can specify the tooling and technologies they would like to use in their MLOps pipeline.
- `AutoMLOps.provision(...)`: Runs provisioning scripts to create and maintain necessary infra for MLOps.
- `AutoMLOps.deprovision(...)`: Runs deprovisioning scripts to tear down MLOps infra created using AutoMLOps.
- `AutoMLOps.deploy(...)`: Builds and pushes component container, then triggers the pipeline job.
- `AutoMLOps.launchAll(...)`: Runs `generate()`, `provision()`, and `deploy()` all in succession.

For a full user-guide, please view these [slides](https://github.com/GoogleCloudPlatform/automlops/blob/main/AutoMLOps_User_Guide.pdf).

# List of Examples

Training
- [00_introduction_training_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/00_introduction_training_example.ipynb) <- start here
- [00_introduction_training_example_no_notebook](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/00_introduction_training_example_no_notebook.py)
- [01_clustering_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/01_clustering_example.ipynb)
- [02_tensorflow_transfer_learning_gpu_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/02_tensorflow_transfer_learning_gpu_example.ipynb)
- [03_bqml_introduction_training_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/03_bqml_introduction_training_example.ipynb)
- [04_bqml_forecasting-retail-demand](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/training/04_bqml_forecasting-retail-demand.ipynb)

Inferencing
- [00_batch_prediction_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/inferencing/00_batch_prediction_example.ipynb)
- [01_customer_churn_model_monitoring_example](https://github.com/GoogleCloudPlatform/automlops/blob/main/examples/inferencing/01_customer_churn_model_monitoring_example.ipynb)

# Supported Tools and Technologies

**Artifact Repositories**: Stores component docker containers
- Artifact Registry

**Deployment Frameworks**: Builds component docker containers, compiles pipelines, and submits Pipeline Jobs
- Cloud Build
- [coming soon] Github Actions
- [coming soon] Gitlab CI
- [coming soon] Bitbucket Pipelines
- [coming soon] Jenkins

**Orchestration Frameworks**: Executes and orchestrates pipelines jobs
- Kubeflow Pipelines (KFP) - Runs on [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction)
- [coming soon] Tensorflow Extended (TFX) - Runs on [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction)
- [coming soon] Argo Workflows - Runs on [GKE](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview)
- [coming soon] Airflow - Runs on [Cloud Composer](https://cloud.google.com/composer/docs)
- [coming soon] Ray - Runs on [GKE](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview)

**Submission Service Compute Environments**: RESTful service for submitting pipeline jobs to the orchestrator (e.g. Vertex AI, Cloud Composer, etc.)
- Cloud Functions
- Cloud Run

**Provisioning Frameworks**: Stands up necessary infra to run MLOps pipelines
- gcloud
- terraform
- [coming soon] pulumi

**Source Code Repositories**: Repository for versioning generated MLOps code
- Cloud Source Repositories
- Bitbucket
- Github
- Gitlab

# Prerequisites
### Generate
In order to use `AutoMLOps.generate(...)`, the following are required:
- Python 3.7 - 3.10
### Provision
In order to use `AutoMLOps.provision(...)` with `provisioning_framework='gcloud'`, the following are recommended:
- [Google Cloud SDK 407.0.0](https://cloud.google.com/sdk/gcloud/reference)
- [beta 2022.10.21](https://cloud.google.com/sdk/gcloud/reference/beta)

In order to use `AutoMLOps.provision(...)` with `provisioning_framework='terraform'`, the following are recommended:
- [Terraform v1.5.6](https://www.terraform.io/downloads.html)

### Deploy
In order to use `AutoMLOps.deploy(...)` with `use_ci=False`, the following are required:
- Local python environment with these packages installed:
    - `kfp<2.0.0`
    - `google-cloud-aiplatform`
    - `google-cloud-pipeline-components`
    - `google-cloud-storage`
    - `pyyaml`

In order to use `AutoMLOps.deploy(...)` with `use_ci=True`, the following are required:
- `git` installed
- `git` logged-in:
```
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
```
- Registered and setup your SSH key if you are using Github, Gitlab, or Bitbucket
- [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/provide-credentials-adc) are set up if you are using Cloud Source Repositories. This can be done through the following commands:
```
gcloud auth application-default login
gcloud config set account <account@example.com>
```

# GCP Services
AutoMLOps makes use of the following products by default:
- [Google Cloud Storage](https://cloud.google.com/storage/docs/introduction)

AutoMLOps will makes use of the following products based on user selected options:

1. if `artifact_repo_type='artifact-registry'`, AutoMLOps will use:
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs/overview)

2. if `use_ci=False` and `orchestration_framework='kfp'` and `deployment_framework='cloud-build'`, AutoMLOps will use:
- [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction)
- [Cloud Build](https://cloud.google.com/build/docs/overview)

2. if `use_ci=True` and `orchestration_framework='kfp'` and `deployment_framework='cloud-build'`, AutoMLOps will use:
- [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction)
- [Cloud Pub/Sub](https://cloud.google.com/pubsub/docs/overview)
- [Cloud Build](https://cloud.google.com/build/docs/overview)
- [Cloud Build Triggers](https://cloud.google.com/build/docs/triggers)

4. if `use_ci=True` and `pipeline_job_submission_service_type='cloud-functions'`, AutoMLOps will use:
- [Cloud Functions](https://cloud.google.com/functions/docs/concepts/overview)

5. if `use_ci=True` and `pipeline_job_submission_service_type='cloud-run'`, AutoMLOps will use:
- [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run)

6. if `use_ci=True` and `schedule_pattern` is specified, AutoMLOps will use:
- [Cloud Scheduler](https://cloud.google.com/scheduler/docs/overview)

7. if `use_ci=True` and `source_repo_type='cloud-source-repositories'`, AutoMLOps will use:
- [Cloud Source Repositories](https://cloud.google.com/source-repositories/docs)


# APIs & IAM
Based on the above user selection, AutoMLOps will enable up to the following APIs during the provision step:
- [aiplatform.googleapis.com](https://cloud.google.com/vertex-ai/docs/reference/rest)
- [artifactregistry.googleapis.com](https://cloud.google.com/artifact-registry/docs/reference/rest)
- [cloudbuild.googleapis.com](https://cloud.google.com/build/docs/api/reference/rest)
- [cloudfunctions.googleapis.com](https://cloud.google.com/functions/docs/reference/rest)
- [cloudresourcemanager.googleapis.com](https://cloud.google.com/resource-manager/reference/rest)
- [cloudscheduler.googleapis.com](https://cloud.google.com/scheduler/docs/reference/rest)
- [cloudtasks.googleapis.com](https://cloud.google.com/tasks/docs/reference/rest)
- [compute.googleapis.com](https://cloud.google.com/compute/docs/reference/rest/v1)
- [iam.googleapis.com](https://cloud.google.com/iam/docs/reference/rest)
- [iamcredentials.googleapis.com](https://cloud.google.com/iam/docs/reference/credentials/rest)
- [ml.googleapis.com](https://cloud.google.com/ai-platform/training/docs/reference/rest)
- [pubsub.googleapis.com](https://cloud.google.com/pubsub/docs/reference/rest)
- [run.googleapis.com](https://cloud.google.com/run/docs/reference/rest)
- [storage.googleapis.com](https://cloud.google.com/storage/docs/apis)
- [sourcerepo.googleapis.com](https://cloud.google.com/source-repositories/docs/reference/rest)


AutoMLOps will create the following service account and update [IAM permissions](https://cloud.google.com/iam/docs/understanding-roles) during the provision step:
1. Pipeline Runner Service Account (defaults to: vertex-pipelines@PROJECT_ID.iam.gserviceaccount.com). Roles added:
- roles/aiplatform.user
- roles/artifactregistry.reader
- roles/bigquery.user
- roles/bigquery.dataEditor
- roles/iam.serviceAccountUser
- roles/storage.admin
- roles/cloudfunctions.admin

# Prechecks and Warnings

AutoMLOps provides a number of optional prechecks and warnings to provide visibility to the user into what IAM permissions are required to run certain operations. 

1. `AutoMLOps.provision(...hide_warnings=False)`: This will check installation versions and account permissions to determine if the current account has the permissions to provision successfully.
2. `AutoMLOps.deploy(...hide_warnings=False)`: This will check installation versions and account permissions to determine if the current account has the permissions to deploy successfully.
2. `AutoMLOps.deploy(...precheck=True)`: This will check for the necessary infrastructure to deploy successfully (e.g. does the specified artifact registry exist, does the specified storage bucket exist, etc.)

# Code Generation Options

AutoMLOps CI/CD options:
1. `use_ci`: Bool that specifies whether to execute using generated files and scripts locally or use cloud CI/CD workflow. Defaults to False. See [CI/CD Workflow](#deployment)

Required parameters:
1. `project_id: str`
2. `pipeline_params: dict`

Optional parameters (defaults shown):
1. `artifact_repo_location: str = 'us-central1'`
2. `artifact_repo_name: str = f'{naming_prefix}-artifact-registry'`
3. `artifact_repo_type: str = 'artifact-registry'`
4. `base_image: str = 'python:3.9-slim'`
5. `build_trigger_location: str = 'us-central1'`
6. `build_trigger_name: str = f'{naming_prefix}-build-trigger'`
7. `custom_training_job_specs: list[dict] = None`
8. `deployment_framework: str = 'cloud-build'`
9. `naming_prefix: str = 'automlops-default-prefix'`
10. `orchestration_framework: str = 'kfp'`
11. `pipeline_job_runner_service_account: str = f'vertex-pipelines@{project_id}.iam.gserviceaccount.com'`
12. `pipeline_job_submission_service_location: str = 'us-central1'`
13. `pipeline_job_submission_service_name: str = f'{naming_prefix}-job-submission-svc'`
14. `pipeline_job_submission_service_type: str = 'cloud-functions'`
15. `provision_credentials_key: str = None`
16. `provisioning_framework: str = 'gcloud'`
17. `pubsub_topic_name: str = f'{naming_prefix}-queueing-svc'`
18. `schedule_location: str = 'us-central1'`
19. `schedule_name: str = f'{naming_prefix}-schedule'`
20. `schedule_pattern: str = 'No Schedule Specified'`
21. `source_repo_branch: str = 'automlops'`
22. `source_repo_name: str = f'{naming_prefix}-repository'`
23. `source_repo_type: str = 'cloud-source-repositories'`
24. `storage_bucket_location: str = 'us-central1'`
25. `storage_bucket_name: str = f'{project_id}-{naming_prefix}-bucket'`
26. `use_ci: bool = False`
27. `vpc_connector: str = 'No VPC Specified'`

Parameter Options:
- `artifact_repo_type=`:
    - 'artifact-registry' (default)
- `deployment_framework=`:
    - 'cloud-build' (default)
    - [coming soon] 'github-actions'
    - [coming soon] 'gitlab-ci'
    - [coming soon] 'bitbucket-pipelines'
    - [coming soon] 'jenkins'
- `orchestration_framework=`:
    - 'kfp' (default)
    - [coming soon] 'tfx'
    - [coming soon] 'argo-workflows'
    - [coming soon] 'airflow'
    - [coming soon] 'ray'
- `pipeline_job_submission_service_type=`:
    - 'cloud-functions' (default)
    - 'cloud-run'
- `provisioning_framework=`:
    - 'gcloud' (default)
    - 'terraform'
    - [coming soon] 'pulumi'
- `source_repo_type=`:
    - 'cloud-source-repositories' (default)
    - 'github'
    - 'gitlab'
    - 'bitbucket'

A description of the parameters is below:
- `project_id`: The project ID.
- `pipeline_params`: Dictionary containing runtime pipeline parameters.
- `artifact_repo_location`: Region of the artifact repo (default use with Artifact Registry).
- `artifact_repo_name`: Artifact repo name where components are stored (default use with Artifact Registry).
- `artifact_repo_type`: The type of artifact repository to use (e.g. Artifact Registry, JFrog, etc.)        
- `base_image`: The image to use in the component base dockerfile.
- `build_trigger_location`: The location of the build trigger (for cloud build).
- `build_trigger_name`: The name of the build trigger (for cloud build).
- `custom_training_job_specs`: Specifies the specs to run the training job with.
- `deployment_framework`: The CI tool to use (e.g. cloud build, github actions, etc.)
- `naming_prefix`: Unique value used to differentiate pipelines and services across AutoMLOps runs.
- `orchestration_framework`: The orchestration framework to use (e.g. kfp, tfx, etc.)
- `pipeline_job_runner_service_account`: Service Account to run PipelineJobs.
- `pipeline_job_submission_service_location`: The location of the cloud submission service.
- `pipeline_job_submission_service_name`: The name of the cloud submission service.
- `pipeline_job_submission_service_type`: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
- `precheck`: Boolean used to specify whether to check for provisioned resources before deploying.
- `provision_credentials_key`: Either a path to or the contents of a service account key file in JSON format.
- `provisioning_framework`: The IaC tool to use (e.g. Terraform, Pulumi, etc.)
- `pubsub_topic_name`: The name of the pubsub topic to publish to.
- `schedule_location`: The location of the scheduler resource.
- `schedule_name`: The name of the scheduler resource.
- `schedule_pattern`: Cron formatted value used to create a Scheduled retrain job.
- `source_repo_branch`: The branch to use in the source repository.
- `source_repo_name`: The name of the source repository to use.
- `source_repo_type`: The type of source repository to use (e.g. gitlab, github, etc.)
- `storage_bucket_location`: Region of the GS bucket.
- `storage_bucket_name`: GS bucket name where pipeline run metadata is stored.
- `hide_warnings`: Boolean used to specify whether to show provision/deploy permission warnings
- `use_ci`: Flag that determines whether to use Cloud CI/CD.
- `vpc_connector`: The name of the vpc connector to use.

AutoMLOps will generate the resources specified by these parameters (e.g. Artifact Registry, Cloud Source Repo, etc.). If use_ci is set to True, AutoMLOps will turn the current working directory of the notebook into a Git repo and use it for the source repo. Additionally, if a cron formatted str is given as an arg for `schedule_pattern` then it will set up a Cloud Schedule to run accordingly.

# Generating Code

AutoMLOps generates code that is compatible with `kfp<2.0.0`. Upon running `AutoMLOps.generate(project_id='project-id', pipeline_params=pipeline_params, use_ci=True)`, a series of directories will be generated automatically:

```bash
.
├── components                                     : Custom vertex pipeline components.
    ├──component_base                              : Contains all the python files, Dockerfile and requirements.txt
        ├── Dockerfile                             : Dockerfile containing all the python files for the components.
        ├── requirements.txt                       : Package requirements for all the python files for the components.
        ├── src                                    : Python source code directory.
            ├──component_a.py                      : Python file containing code for the component.
            ├──...(for each component)
    ├──component_a                                 : Components specs generated using AutoMLOps
        ├── component.yaml                         : Component yaml spec, acts as an I/O wrapper around the Docker container.
    ├──...(for each component)
├── configs                                        : Configurations for defining vertex ai pipeline and MLOps infra.
    ├── defaults.yaml                              : Runtime configuration variables.
├── images                                         : Custom container images for training models (optional).
├── pipelines                                      : Vertex ai pipeline definitions.
    ├── pipeline.py                                : Full pipeline definition; compiles pipeline spec and uploads to GCS.
    ├── pipeline_runner.py                         : Sends a PipelineJob to Vertex AI.
    ├── requirements.txt                           : Package requirements for running pipeline.py.
    ├── runtime_parameters                         : Variables to be used in a PipelineJob.
        ├── pipeline_parameter_values.json         : Json containing pipeline parameters.
├── provision                                      : Provision configurations and details.
    ├── provision_resources.sh                     : Provisions the necessary infra to run the MLOps pipeline.
    ├── provisioning_configs                       : (Optional) Relevant terraform/Pulumi config files for provisioning infa.
├── scripts                                        : Scripts for manually triggering the cloud run service.
    ├── build_components.sh                        : Submits a Cloud Build job that builds and pushes the components to the registry.
    ├── build_pipeline_spec.sh                     : Compiles the pipeline specs.
    ├── run_pipeline.sh                            : Submit the PipelineJob to Vertex AI.
    ├── run_all.sh                                 : Builds components, compiles pipeline specs, and submits the PipelineJob.
    ├── publish_to_topic.sh                        : Publishes a message to a Pub/Sub topic to invoke the pipeline job submission service.
├── services                                       : MLOps services related to continuous training.
    ├── submission_service                         : REST API service used to submit pipeline jobs to Vertex AI.
        ├── Dockerfile                             : Dockerfile for running the REST API service.
        ├── requirements.txt                       : Package requirements for the REST API service.
        ├── main.py                                : Python REST API source code.
├── README.md                                      : Readme markdown file describing the contents of the generated directories.
└── cloudbuild.yaml                                : Cloudbuild configuration file for building custom components.
```

# Provisioning
AutoMLOps currently provides 2 primary options for provisioning infrastructure: `gcloud` and `terraform`. In the diagram below dashed boxes show areas users can select and customize their tooling. 

<p align="center">
    <img src="https://raw.githubusercontent.com/GoogleCloudPlatform/automlops/main/assets/provision/provision-default.png" alt="CICD" width="1000"/>
</p>


# Deployment
### Cloud Continuous Integration and Continuous Deployment Workflow
If `use_ci=True`, AutoMLOps will generate and use a fully featured CI/CD environment for the pipeline. Otherwise, it will use the local scripts to build and run the pipeline. In the diagrams below dashed boxes show areas users can select and customize their tooling. 

**<center>Cloud Build option:</center>**
<p align="center">
    <img src="https://raw.githubusercontent.com/GoogleCloudPlatform/automlops/main/assets/deploy/CICD-default.png" alt="CICD" width="1000"/>
</p>

**<center>Github Actions option:</center>**
<p align="center">
    <img src="https://raw.githubusercontent.com/GoogleCloudPlatform/automlops/main/assets/deploy/CICD-github.png" alt="CICD" width="1000"/>
</p>

**<center>Gitlab CI option:</center>**
<p align="center">
    <img src="https://raw.githubusercontent.com/GoogleCloudPlatform/automlops/main/assets/deploy/CICD-gitlab.png" alt="CICD" width="1000"/>
</p>

**<center>Bitbucket Pipelines option:</center>**
<p align="center">
    <img src="https://raw.githubusercontent.com/GoogleCloudPlatform/automlops/main/assets/deploy/CICD-bitbucket.png" alt="CICD" width="1000"/>
</p>

# Other Customizations

**Set scheduled run:**

Use the `schedule_pattern` parameter to specify a cron job schedule to run the pipeline job on a recurring basis.
```
schedule_pattern = '0 */12 * * *'
```

**Set pipeline compute resources:**

Use the `base_image` and `custom_training_job_specs` parameter to specify resources for any custom component in the pipeline.
```
base_image = 'us-docker.pkg.dev/vertex-ai/training/tf-gpu.2-11.py310:latest',
custom_training_job_specs = [{
    'component_spec': 'train_model',
    'display_name': 'train-model-accelerated',
    'machine_type': 'a2-highgpu-1g',
    'accelerator_type': 'NVIDIA_TESLA_A100',
    'accelerator_count': 1
}]
```

**Use a VPC connector:**

Use the `vpc_connector` parameter to specify a vpc connector.
```
vpc_connector = 'example-vpc-connector'
```

**Specify package versions:**

Use the `packages_to_install` parameter of `@AutoMLOps.component` to explicitly specify packages and versions.
```
@AutoMLOps.component(
    packages_to_install=[
        "google-cloud-bigquery==2.34.4",
        "pandas",
        "pyarrow",
        "db_dtypes"
    ]
)
def create_dataset(
    bq_table: str,
    data_path: str,
    project_id: str
):
...
```

# Contributors

[Sean Rastatter](mailto:srastatter@google.com): Tech Lead

[Tony DiLoreto](mailto:tonydiloreto@google.com): Project Manager

[Allegra Noto](mailto:allegranoto@google.com): Senior Project Engineer

[Ahmad Khan](mailto:ahmadkh@google.com): Engineer

[Jesus Orozco](mailto:jesusfc@google.com): Cloud Engineer

[Erin Horning](mailto:ehorning@google.com): Infrastructure Engineer

[Alex Ho](mailto:alexanderho@google.com): Engineer

[Kyle Sorensen](mailto:kylesorensen@google.com): Cloud Engineer

# Disclaimer

**This is not an officially supported Google product.**

Copyright 2023 Google LLC. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
