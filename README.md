# 1-Click MLOps

1-Click MLOps is a tool that generates a production-style MLOps pipeline from Jupyter Notebooks.

The tool currently operates as a local package import, with the end goal of becoming a Jupyter plugin to Vertex Workbench managed notebooks. The tool will generate yaml-component definitions, complete with Dockerfiles and requirements.txts for all Kubeflow components defined in a notebook. It will also generate a series of directories to support the creation of Vertex Pipelines.

Included in the repository is an [example notebook](./coloring_book.ipynb) that demonstrates the usage of the tool. Upon running `OneClickMLOps.go(project_id='sandbox-srastatter',pipeline_params=pipeline_params)`, a series of directories will be generated automatically, and a pipelineJob will be submitted using the setup below:

```bash
.
├── components                                     : Custom vertex pipeline components.
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

# Next Steps
- Add docstrings, refactor and component code
- Add unit tests to code
- Use [terraform](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples/tree/main/terraform) for the creation of GS buckets, Artifact registries, assignment of IAM privileges, and creation of service accounts for running the pipeline.
- LONG-TERM: Remove the need to know/use Kubeflow all together (i.e. import kfp need not be necessary)

# Contributors:

[srastatter@](https://moma.corp.google.com/person/srastatter@google.com): Technical Lead

[tonydiloreto@](https://moma.corp.google.com/person/tonydiloreto@google.com): Project Lead