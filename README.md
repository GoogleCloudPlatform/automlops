# AutoMLOps

AutoMLOps is a tool that generates a production ready MLOps pipeline from Jupyter Notebooks, bridging the gap between Data Science and DevOps and accelerating the adoption and use of Vertex AI. The tool generates an MLOps codebase for users to customize, and provides a way to build and manage a CI/CD integrated MLOps pipeline from the notebook. The tool automatically builds a source repo for versioning, cloudbuild configs and triggers, an artifact registry for storing custom components, gs buckets, service accounts and updated IAM privs for running pipelines, enables APIs (cloud Run, Cloud Build, Artifact Registry, etc.), creates a runner service API in Cloud Run for submitting PipelineJobs to Vertex AI, and a Cloud Scheduler job for submitting PipelineJobs on a recurring basis. These automatic integrations empower data scientists to take their experiments to production more quickly, allowing them to focus on what they do best: providing actionable insights through data.

# Prerequisites

In order to use AutoMLOps, the following are required:

- Jupyter (or Jupyter-compatible) notebook environment
- [Notebooks API](https://pantheon.corp.google.com/marketplace/product/google/notebooks.googleapis.com) enabled
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

# APIs & IAM
The tool will enable the following APIs:
- cloudresourcemanager.googleapis.com
- aiplatform.googleapis.com
- artifactregistry.googleapis.com
- cloudbuild.googleapis.com
- cloudscheduler.googleapis.com
- compute.googleapis.com
- iam.googleapis.com
- iamcredentials.googleapis.com
- ml.googleapis.com
- run.googleapis.com
- storage.googleapis.com
- sourcerepo.googleapis.com

The tool will update IAM priviledges for the following accounts:
1. Pipeline Runner Service Account (one is created if it does exist, defaults to: vertex-pipelines@automlops-sandbox.iam.gserviceaccount.com). Roles added:
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

For a user-guide, please view these [slides](https://docs.google.com/presentation/d/1suAfces32N098MOzme4LA084P3vA3iJ6hMmQfn1-7Wo/edit?usp=sharing).

# Options

The tool current supports 4 different configurations based on the following flags:
1. `use_kfp_spec`: (Optional) Bool that specifies whether to use Kubeflow definitions or Python custom definitions. Defaults to False. See [user guide](https://docs.google.com/presentation/d/1suAfces32N098MOzme4LA084P3vA3iJ6hMmQfn1-7Wo/edit?usp=sharing).
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
15. `schedule_location: str = ' us-central1'`
16. `schedule_name: str = 'AutoMLOps-schedule'`
17. `schedule_pattern: str = 'No Schedule Specified'`
18. `use_kfp_spec: bool = False`

The tool will generate the resources specified by these parameters (e.g. Artifact Registry, Cloud Source Repo, etc.). If run_local is set to False, the tool will turn the current working directory of the notebook into a Git repo and use it for the CSR. Additionally, if a cron formatted str is given as an arg for `schedule_pattern` then it will set up a Cloud Schedule to run accordingly. 

# Layout

Included in the repository is an [example notebook](./example/coloring_book.ipynb) that demonstrates the usage of the tool. Upon running `AutoMLOps.go(project_id='sandbox-srastatter',pipeline_params=pipeline_params)`, a series of directories will be generated automatically, and a pipelineJob will be submitted using the setup below:

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
    ├── run_pipeline.sh                            : Submit the PipelineJob to Vertex AI.
    ├── run_all.sh                                 : Builds components, pipeline specs, and submits the PipelineJob.
└── cloudbuild.yaml                                : Cloudbuild configuration file for building custom components.
```

This tool makes use of the following products by default:
- Vertex AI Pipelines
- Artifact Registry
- Google Cloud Storage
- Cloud Build
- Cloud Build Triggers
- Cloud Run
- Cloud Scheduler

# Cloud Continuous Integration and Continuous Deployment Workflow
If `run_local=False`, the tool will generate and use a fully featured CI/CD environment for the pipeline. Otherwise, it will use the local scripts to build and run the pipeline.

<p align="center">
    <img src="./CICD.png" alt="CICD" width="800"/>
</p>

# Next Steps / Backlog
- Verify delivery mechanism (setup.py with wheel)
- Improve documentation
- Add unit tests
- Use [terraform](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples/tree/main/terraform) for the creation of resources.
- Allow multiple AutoMLOps pipelines within the same directory
- Adding model monitoring part
- Look into alternatives to Pipreqs

# Contributors

[Sean Rastatter](mailto:srastatter@google.com): Technical Lead

[Tony Diloreto](mailto:tonydiloreto@google.com): Project Manager

[Allegra Noto](mailto:allegranoto@google.com): Engineer