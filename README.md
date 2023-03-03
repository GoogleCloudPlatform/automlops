# AutoMLOps

AutoMLOps is a service that generates a production ready MLOps pipeline from Jupyter Notebooks, bridging the gap between Data Science and DevOps and accelerating the adoption and use of Vertex AI. The service generates an MLOps codebase for users to customize, and provides a way to build and manage a CI/CD integrated MLOps pipeline from the notebook. AutoMLOps automatically builds a source repo for versioning, cloudbuild configs and triggers, an artifact registry for storing custom components, gs buckets, service accounts and updated IAM privs for running pipelines, enables APIs (Cloud Run, Cloud Build, Artifact Registry, etc.), creates a runner service API in Cloud Run for submitting PipelineJobs to Vertex AI, and a Cloud Scheduler job for submitting PipelineJobs on a recurring basis. These automatic integrations empower data scientists to take their experiments to production more quickly, allowing them to focus on what they do best: providing actionable insights through data.

# Prerequisites

In order to use AutoMLOps, the following are required:

- Jupyter (or Jupyter-compatible) notebook environment
- [Notebooks API](https://console.cloud.google.com/marketplace/product/google/notebooks.googleapis.com) enabled
- Python 3.0 - 3.10
- [Google Cloud SDK 407.0.0](https://cloud.google.com/sdk/gcloud/reference)
- [beta 2022.10.21](https://cloud.google.com/sdk/gcloud/reference/beta)
- `git` installed
- `git` logged-in:
```
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
```
- [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/provide-credentials-adc) are setup. This can be done through the following commands:
```
gcloud auth application-default login
gcloud config set account <account@example.com>
```

# Install

Clone the repo and install either via setup.py or wheel (wheel requires less processing):
- setup.py: `pip install .`
- wheel: `pip install dist/AutoMLOps-1.0.0-py2.py3-none-any.whl`

# Dependencies
- `autoflake==2.0.0`,
- `docopt==0.6.2`,
- `ipython==7.34.0`,
- `pipreqs==0.4.11`,
- `pyflakes==3.0.1`,
- `PyYAML==5.4.1`,
- `yarg==0.1.9`

# GCP Services

AutoMLOps makes use of the following Google Cloud services by default:
- [Vertex AI Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/introduction)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs/overview)
- [Google Cloud Storage](https://cloud.google.com/storage/docs/introduction)
- [Cloud Build](https://cloud.google.com/build/docs/overview)
- [Cloud Build Triggers](https://cloud.google.com/build/docs/triggers)
- [Cloud Run](https://cloud.google.com/run/docs/overview/what-is-cloud-run)
- [Cloud Scheduler](https://cloud.google.com/scheduler/docs/overview)

# APIs & IAM
AutoMLOps will enable the following APIs:
- [cloudresourcemanager.googleapis.com](https://cloud.google.com/resource-manager/reference/rest)
- [aiplatform.googleapis.com](https://cloud.google.com/vertex-ai/docs/reference/rest)
- [artifactregistry.googleapis.com](https://cloud.google.com/artifact-registry/docs/reference/rest)
- [cloudbuild.googleapis.com](https://cloud.google.com/build/docs/api/reference/rest)
- [cloudscheduler.googleapis.com](https://cloud.google.com/scheduler/docs/reference/rest)
- [compute.googleapis.com](https://cloud.google.com/compute/docs/reference/rest/v1)
- [iam.googleapis.com](https://cloud.google.com/iam/docs/reference/rest)
- [iamcredentials.googleapis.com](https://cloud.google.com/iam/docs/reference/credentials/rest)
- [ml.googleapis.com](https://cloud.google.com/ai-platform/training/docs/reference/rest)
- [run.googleapis.com](https://cloud.google.com/run/docs/reference/rest)
- [storage.googleapis.com](https://cloud.google.com/storage/docs/apis)
- [sourcerepo.googleapis.com](https://cloud.google.com/source-repositories/docs/reference/rest)

AutoMLOps will update [IAM privileges](https://cloud.google.com/iam/docs/understanding-roles) for the following accounts:
1. Pipeline Runner Service Account (one is created if it does exist, defaults to: vertex-pipelines@PROJECT_ID.iam.gserviceaccount.com). Roles added:
- roles/aiplatform.user
- roles/artifactregistry.reader
- roles/bigquery.user
- roles/bigquery.dataEditor
- roles/iam.serviceAccountUser
- roles/storage.admin
- roles/run.admin
2. Cloudbuild Default Service Account (PROJECT_NUMBER@cloudbuild.gserviceaccount.com). Roles added:
- roles/run.admin
- roles/iam.serviceAccountUser
3. Executing Account (current gcloud account, can be viewed by running the command `gcloud config list account`). Roles added:
- roles/iam.serviceAccountTokenCreator
- roles/iam.serviceAccountUser

# User Guide

For a user-guide, please view these [slides](./AutoMLOps_Implementation_Guide_External.pdf).

# Options

AutoMLOps currently supports 4 different configurations based on the following flags:
1. `use_kfp_spec`: (Optional) Bool that specifies whether to use Kubeflow definitions or Python custom definitions. Defaults to False. See [user guide](./AutoMLOps_Implementation_Guide_External.pdf).
    - if True:
        - The pipeline uses Kubeflow objects and syntax, and will generate all the necessary files in the backend to compile and run the pipeline.
    - if False:
        - The pipeline uses a custom defined syntax (through a series of python dictionaries and lists) that effectively removes the need to know Kubeflow syntax to compile and run the pipeline. 
2. `run_local`: (Optional) Bool that specifies whether to use generate files resources locally or use cloud CI/CD workflow (see below). Defaults to True. See [CI/CD Workflow](#cloud-continuous-integration-and-continuous-deployment-workflow)

Required parameters:
1. `project_id: str`
2. `pipeline_params: dict`

Optional parameters (defaults shown):
1. `af_registry_location: str = 'us-central1'`
2. `af_registry_name: str = 'vertex-mlops-af'`
3. `cb_trigger_location: str = 'us-central1'`
4. `cb_trigger_name: str = 'automlops-trigger'`
5. `cloud_run_location: str = 'us-central1'`
6. `cloud_run_name: str = 'run-pipeline'`
7. `csr_branch_name: str = 'automlops'`
8. `csr_name: str = 'AutoMLOps-repo'`
9. `gs_bucket_location: str = 'us-central1'`
10. `gs_bucket_name: str = None`
11. `parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json'`
12. `pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json'`
13. `pipeline_runner_sa: str = None`
14. `run_local: bool = True`
15. `schedule_location: str = 'us-central1'`
16. `schedule_name: str = 'AutoMLOps-schedule'`
17. `schedule_pattern: str = 'No Schedule Specified'`
18. `use_kfp_spec: bool = False`

AutoMLOps will generate the resources specified by these parameters (e.g. Artifact Registry, Cloud Source Repo, etc.). If run_local is set to False, the AutoMLOps will turn the current working directory of the notebook into a Git repo and use it for the CSR. Additionally, if a cron formatted str is given as an arg for `schedule_pattern` then it will set up a Cloud Schedule to run accordingly. 

# Layout

Included in the repository is an [example notebook](./example/automlops_example_notebook.ipynb) that demonstrates the usage of AutoMLOps. Upon running `AutoMLOps.go(project_id='automlops-sandbox',pipeline_params=pipeline_params)`, a series of directories will be generated automatically, and a pipelineJob will be submitted using the setup below:

```bash
.
├── cloud_run                                      : Cloud Runner service for submitting PipelineJobs.
    ├──run_pipeline                                : Contains main.py file, Dockerfile and requirements.txt
├── components                                     : Custom vertex pipeline components.
    ├──component_base                              : Contains all the python files, Dockerfile and requirements.txt
    ├──create_dataset                              : Pull data from a BQ table and writes it as a csv to GS.
    ├──train_model                                 : Trains a basic decision tree classifier.
    ├──deploy_model                                : Deploys model to endpoint.
├── images                                         : Custom container images for training models.
├── pipelines                                      : Vertex ai pipeline definitions.
    ├── pipeline.py                                : Full pipeline definition.
    ├── pipeline_runner.py                         : Sends a PipelineJob to Vertex AI.
    ├── runtime_parameters                         : Variables to be used in a PipelineJob.
        ├── pipeline_parameter_values.json         : Json containing pipeline parameters.    
├── configs                                        : Configurations for defining vertex ai pipeline.
    ├── defaults.yaml                              : PipelineJob configuration variables.
├── scripts                                        : Scripts for manually triggering the cloud run service.
    ├── build_components.sh                        : Submits a Cloud Build job that builds and deploys the components.
    ├── build_pipeline_spec.sh                     : Builds the pipeline specs
    ├── create_resources.sh                        : Creates an artifact registry and gs bucket if they do not already exist.
    ├── create_scheduler.sh                        : Creates a cloud scheduler resources to submit a PipelineJob.
    ├── submit_to_runner_svc.sh                    : Sends a json file to the Cloud runner service to submit a PipelineJob.
    ├── run_pipeline.sh                            : Submit the PipelineJob to Vertex AI.
    ├── run_all.sh                                 : Builds components, pipeline specs, and submits the PipelineJob.
└── cloudbuild.yaml                                : Cloudbuild configuration file for building custom components.
```

# Cloud Continuous Integration and Continuous Deployment Workflow
If `run_local=False`, AutoMLOps will generate and use a fully featured CI/CD environment for the pipeline. Otherwise, it will use the local scripts to build and run the pipeline.

<p align="center">
    <img src="./CICD.png" alt="CICD" width="800"/>
</p>

# Pipeline Components

AutoMLOps comes with a sample [Coloring Book](example/automlops_example_notebook.ipynb) with 4 components as part of the pipeline. 
Sample code for commonly used services:

- [Feature Store](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official/feature_store)
- [BigQuery ML](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official/bigquery_ml)
- [Model Registry](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official/model_registry)
- [Experiments](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official/experiments)
- [ExplainableAI](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official/explainable_ai)

More components can be found in the [Official VertexAI Component Repository](https://github.com/GoogleCloudPlatform/vertex-ai-samples/tree/main/notebooks/official).

# Next Steps / Backlog

The following are known improvements for upcoming releases. Users may contribute to the project either by cloning the repo and making pull requests, or opening up [issues](https://github.com/GoogleCloudPlatform/automlops/issues) directly.

- PyPI
- Refine unit tests
- Use [terraform](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples/tree/main/terraform) for the creation of resources.
- Allow multiple AutoMLOps pipelines within the same directory
- Adding model monitoring part
- Alternatives to Pipreqs

# Contributors

[Sean Rastatter](mailto:srastatter@google.com): Technical Lead

[Tony DiLoreto](mailto:tonydiloreto@google.com): Project Manager

[Allegra Noto](mailto:allegranoto@google.com): Engineer


# Contributing
See the contributing [instructions](/CONTRIBUTING.md) to get started contributing.

# License
All solutions within this repository are provided under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) license. Please see the [LICENSE](/LICENSE) file for more detailed terms and conditions.

# Disclaimer

**This repository and its contents are not an official Google Product.**

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