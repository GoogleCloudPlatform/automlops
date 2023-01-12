# AutoMLOps

AutoMLOps is a tool that generates a production ready MLOps pipeline from Jupyter Notebooks, bridging the gap between Data Science and DevOps and accelerating the adoption and use of Vertex AI. The tool generates an MLOps codebase for users to customize, and provides a way to build and manage a CI/CD integrated MLOps pipeline from the notebook. The tool automatically builds a source repo for versioning, cloudbuild configs and triggers, an artifact registry for storing custom components, gs buckets, service accounts and updated IAM privs for running pipelines, enables APIs (cloud Run, Cloud Build, Artifact Registry, etc.), creates a runner service API in Cloud Run for submitting PipelineJobs to Vertex AI, and a Cloud Scheduler job for submitting PipelineJobs on a recurring basis. These automatic integrations empower data scientists to take their experiments to production more quickly, allowing them to focus on what they do best: providing actionable insights through data.

The tool must be used in a Jupyter Notebook.

# Install

Clone the repo and install either via setup.py or wheel (wheel requires less processing):
- setup.py: `pip install .`
- wheel: `pip install dist/AutoMLOps-1.0.0-py2.py3-none-any.whl`

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
3. `gs_bucket_location: str = 'us-central1'`
4. `gs_bucket_name: str = None`
5. `csr_name: str = 'AutoMLOps-repo'`
6. `schedule: str = 'No Schedule Specified'` # must be cron formatted
7. `schedule_location: str = 'us-central1'`
8. `parameter_values_path: str = 'pipelines/runtime_parameters/pipeline_parameter_values.json'`
9. `pipeline_job_spec_path: str = 'scripts/pipeline_spec/pipeline_job.json'`
10. `pipeline_runner_sa: str = None`
11. `use_kfp_spec: bool = False` # see above
12. `run_local: bool = True` # see above

The tool will generate the resources specified by these parameters (e.g. Artifact Registry, Cloud Source Repo, etc.). If run_local is set to False, the tool will turn the current working directory of the notebook into a Git repo and use it for the CSR. Additionally, if a cron formatted str is given as an arg for `schedule` then it will set up a Cloud Schedule to run accordingly. 

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
- Improve this documentation
- Add unit tests to code
- Use [terraform](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples/tree/main/terraform) for the creation of GS buckets, Artifact registries, assignment of IAM privileges, creation of service accounts, etc. for running the pipeline.
- Allow multiple AutoMLOps pipelines within the same directory
- Pub/Sub topic for cloud runner service?
- Forwarding errors from subprocess.run()
- Adding in model monitoring parts...?
- Provide resource links (e.g. pipelineJobs, cloud scheduler jobs, etc) as outputs in the Jupyter Notebook
- Decide whether to add a [contributing file](go/releasing/preparing#CONTRIBUTING)
- Decide whether to include apache license headers on generated code (not required according to [this](go/releasing/preparing#license-headers))
- Pipreqs is problematic...
- Using $(gcloud auth print-identity-token --quiet) to generate auth tokens is a hack

# Contributors

[srastatter@](https://moma.corp.google.com/person/srastatter@google.com): Technical Lead

[tonydiloreto@](https://moma.corp.google.com/person/tonydiloreto@google.com): Project Manager