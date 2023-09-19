# Change Log
All notable changes to this project will be documented in this file.

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