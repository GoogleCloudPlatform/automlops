# Change Log
All notable changes to this project will be documented in this file.

## [1.3.1] - 2024-10-30

### Added

- Guide explaining how to set up Workload Identity Federation for AutoMLOps
- Created new docs/ directory

### Changed

- Made `github` and `github-actions` the default options for `source_repo_type` and `deployment_framework` respectively
- Updated example notebooks so that they are set to `use_ci=False` by default
- Provided samples in the example notebooks that demonstrate how to use the `github` and `github_actions` setup
- Added a guide for setting up Workload Identity Federation
- Updated github actions op versions (checkout and auth)

### Fixed

- Fixed broken default of now deprecated Cloud Source Repositories
- Updated sklearn version of training example00 to use v1.3
- Removed `build_trigger_location` from resources manifest output

## [1.3.0] - 2024-5-22

### Added

### Changed

- Refactored code to follow OOP paradigm
- Made `kfp` a required dependency of AutoMLOps
- kfp v2 code is now generated and required for use with AutoMLOps; before this version, `kfp<2.0.0` was required. kfp v2 is not always backwards compatibile with v1
- Removed support for reading/writing kfp components directly. AutoMLOps now only supports our standard `AutoMLOps.component` and `AutoMLOps.pipeline` syntax rather than `dsl.component`
- Removed requirement that input parameters for `AutoMLOps.component` be python primitives only
- Removed the need for `.AutoMLOps-cache`; files are no longer written to an itermediary location and stored in memory instead
- Updated examples directory to support new changes/updates

### Fixed

## [1.2.9] - 2024-1-18

### Added

- Added `setup_model_monitoring` parameter to `AutoMLOps.generate` and orchestration/configs.py
- Added the creation of a model_monitoring/ directory and `create_model_monitoring_job.sh` script to generate
- Added a new `AutoMLOps.monitor` function, along with relevant templates and tests
- Added in a monitoring section into the generated `config/defaults.yaml` file
- Added `logging.googleapis.com` to the list of potentially required apis.
- Created 2 new functions for giving warnings when running `AutoMLOps.monitor`: `get_model_monitoring_min_permissions` and `get_model_monitoring_recommended_roles` in utils.py

### Changed

- Updated the `services/submission_service/main.py.j2` to include elements for automatic retraining based on monitoring anomaly logs, and adding in labels to the submit.
- Updated `services/submission_service/requirements.txt` to include google-cloud-storage.
- Updated the `README.md.j2` to reflect the optional creation of the new model_monitoring/ directory.
- Changed the format for how `config/defaults.yaml` file gets written; this file is now written using the `write_yaml_file` function (yaml.safe_dump) in utils.py.
- Updated the `account_permissions_warning` function in utils.py to include a new operation: `operation='model_monitoring'`
- Updated the introductory example, readme, and user guide to reflect the new monitoring capabilities.
- Renamed `validate_schedule` in utils.py to `validate_use_ci` to reflect new requirements for model monitoring.

### Fixed

## [1.2.8] - 2024-1-09

### Added

- Support for Output annotations with AutoMLOps.component

### Changed

### Fixed

## [1.2.7] - 2023-11-06

### Added

### Changed

- Updated state_bucket naming schema
- Updated unit tests to reflect state_bucket naming schema
- Updated outputs.tf block to not include csr if use_ci=False

### Fixed


## [1.2.6] - 2023-10-05

### Added

### Changed

- Updated default to not disable api services
- Changed required_permissions and recommend_roles from set to list
- Updated required_permissions and recommend_roles lists to be dynamic based on user tooling selection
- Changed google_project_iam_member block to use a local list for setting iam roles
- Moved csr creation to only occur if use_ci=True
- Updated github_actions config to use source_repo_branch parameter into of default `automlops` branch

### Fixed

- Fixed run local issue regarding dockerfile pathing
- Fixed cloudbuild trigger terraform bug with ignored_files


## [1.2.5] - 2023-10-05

### Added

### Changed

### Fixed

- Fixed bug with generating .github/workflows directories


## [1.2.4] - 2023-10-03

### Added

### Changed

- Only will create .github/ directory if using github-actions

### Fixed

- Pinned the python docker container step for the cloudbuild yaml to python:3.10, this address some dependency issues with the latest python docker image


## [1.2.3] - 2023-09-29

### Added

- Support for Github Actions integration
- Added workload identity federation integration

### Changed

- Updated documentation
- .git and relevant files are now placed inside the AutoMLOps/ base directory

### Fixed

- Set default cloud functions registry to the artifact-registry that is created as part of the provision operation


## [1.2.2] - 2023-09-25

### Added

### Changed

- Commented out change from 1.2.1 to set cloud functions default registry to artifact-registry; there appears to be an auth bug with this setting
- Updated documentation

### Fixed
 
- Removed legacy ml.googleapis.com API that is deprecated as of 9/25/2023


## [1.2.1] - 2023-09-20

### Added

- Support for Vertex AI experiments
- Added in an include statement for the build trigger (only runs on changes to AutoMLOps/**)
 
### Changed

- Set default cloud functions registry to artifact-registry
- Changed recommended roles and permissions for deploying with `use_ci=False`.

### Fixed
 
- Fixed issues with `use_ci=False` provision directory not being created properly
- Fixed issues with `use_ci=False` terraform config


## [1.2.0] - 2023-09-13

### Added

Major version updates:
- Code is now broken down into 5 main operations: generate, provision, deprovision, deploy, and launchAll
- Uses jinja2 templates for storing code templates and writing to files
- Additional package dependencies using Jinja2 templates and deploying with precheck function
- Provides additional warnings and checks for giving IAM permissions visibility to the user
- Creates a .gitignore by default
- Support for cloud-functions in addition to cloud-run for the submission service
- Added 2 new generated folders: provision/ and services/
- Added naming_prefix parameter to allow for differentiating between AutoMLOps pipelines in the same project
- Significant generalization in terms of tooling (now allows for specifying provisioning_frameworks, deployment_frameworks, etc.)
- Renamed backend src code folder to google_cloud_automlops to avoid naming confusion
- Added enum and config files, which is different than previous approach of class inheritance
 
### Changed

- Updated README.md and documentation
- Templatized code has now been pulled out and placed into jinja2 templates.
- Gitops workflow placed into separate folder and file, will only version AutoMLOps/ directory instead of the whole cwd.
- Reworked deployment workflow and build configuration (submission service and cloud scheduler are now created as part of the provision step).
- Update notebook examples
- Changed wording and branding descriptions
- Significant updates to unit tests

### Fixed
 
- Bugs related to provisioning with terraform


## [1.1.4] - 2023-07-25

### Added

- Writes .gitkeep to scripts/pipeline_spec directory by default
- Generates a readme.md into generated AutoMLOps codebase now by default
 
### Changed
 
- Two newlines after functions (linting)
- Parameter mapping (list -> JsonArray, map -> JsonObject)
- Updated documentation: added examples section into main readme, changed package version deps in examples notebooks

### Fixed
 
- Migration issues with pyyaml 5.4.1 since release of cython>3.0; Fixed by updating pyyaml version to 6.0.1.

## [1.1.3] - 2023-07-07

### Added
- Added a BQML retail notebook example
- Major unit tests added for kfp framework and cloudbuild deployments
 
### Changed
 
- Updated the git workflow to check that the remote is pointing to the correct project id.

### Fixed
 
- Pinned all kfp versions to `kfp<2.0.0.` to address the recent migration to kfp2+.

## [1.1.2] - 2023-05-26

### Added
- Added in optional parameter for specifying a base_image.
- Created an example notebook that walks the user through a transfer learning example using a GPU.
- Added in a `clear_cache` function which deletes all files within the tmpfiles directory.
 
### Changed

- Updated readme and implementation guide.
- Long-term change: .tmpfiles/ subdirectory to .AutoMLOps-cache/
- Long-term change: removed `use_kfp_spec` from parameter lists and switched to determining this at run-time.

### Fixed
 
- Removed redundant code for cloudbuild config generation.
- Updated constants.py file to remove constants no longer being used.
- Fixed custom imports mismatch between kfp spec and custom automlops spec.
- Verified custom_training_jobs_specs works as intended. 

## [1.1.1] - 2023-05-17

### Added
- Refactored backend modules to be structured based on frameworks (e.g. kfp, tfx, etc.) and deployments (e.g. cloudbuild, github actions, etc.)
- Added some unit tests for the utils.py module.
 
### Changed

- Moved unit tests to /tests directory.

## [1.1.0] - 2023-04-28

### Added
- New interface for defining AutoMLOps components and Pipelines. Removed the need to call Jupyter cell decorators and replaced them with Python function based decorators instead.
- New feature updates allow for running AutoMLOps outside of Jupyter Notebooks.
- Examples for running AutoMLOps outside of a notebook, as well as an example inferencing pipeline.
- Faster build jobs
 
### Changed

- Updated readme and implementation guide.
- Better logging
- Better handling of requirements.txt (remove dups, infer from pipreqs, option to input explicit versions, sorted order)
- Better versioning of models

### Fixed
 
- Bug that can change current working directory on failure with run_local=True.

## [1.0.5] - 2023-03-06

Official release on PyPI.

## [1.0.3] - 2023-03-06

Staging for PyPI.

### Changed
  
- Cleaning up wheel and egg files from repo.
- Remove dist/ and build/ directories.

## [1.0.2] - 2023-03-06

Added feature to allow for accelerated/distributed model training.
 
### Added
- Support for custom training job specs (specifies which resources to use for pipeline jobs).
 
### Changed
  
- Updated readme and implementation guide.
- New custom_training_job_specs parameter.
- Changed workflow for PipelineBuilder
 
### Fixed
 
- Bug related to grep substring match for create_resources script.

## [1.0.1] - 2023-02-01

Reworked process to submit jobs to cloud runner service.
 
### Added
- Cloud Tasks Queue; API enabling, queue creation, and task generation.
 
### Changed
  
- run() workflow reduced; submission to cloud runner service now takes place as part of the cloudbuild script.
- Creation of schedule job is now part of the cloudbuild script. 
- Removed submit_to_runner_svc.sh and create_scheduler.sh.
- Added support for vpc_connectors.
 
### Fixed
 
- Bug related to waiting for cloudbuild job to complete before submitting to cloud runner service.
- Bug related to elevated IAM privileges in order to authenticate before submitting to cloud runner service. 
 
## [1.0.0] - 2023-01-19

First major release