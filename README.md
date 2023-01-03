# AutoMLOps

AutoMLOps is a tool that generates a production-style MLOps pipeline from Jupyter Notebooks.
The tool currently operates as a local package import, with the end goal of becoming a Jupyter plugin to Vertex Workbench managed notebooks. The tool will generate yaml-component definitions, complete with Dockerfiles and requirements.txts for all Kubeflow components defined in a notebook. It will also generate a series of directories to support the creation of Vertex Pipelines.

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

Included in the repository is an [example notebook](./v2/coloring_book.ipynb) that demonstrates the usage of the tool. Upon running `AutoMLOps.go(project_id='sandbox-srastatter',pipeline_params=pipeline_params)`, a series of directories will be generated automatically, and a pipelineJob will be submitted using the setup below:

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

# Next Steps
- Package code for delivery (use setup.py?)
- Improve this documentation
- Add unit tests to code
- Use [terraform](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples/tree/main/terraform) for the creation of GS buckets, Artifact registries, assignment of IAM privileges, creation of service accounts, etc. for running the pipeline.

# Contributors

[srastatter@](https://moma.corp.google.com/person/srastatter@google.com): Technical Lead

[tonydiloreto@](https://moma.corp.google.com/person/tonydiloreto@google.com): Project Manager