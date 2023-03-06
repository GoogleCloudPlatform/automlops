# Change Log
All notable changes to this project will be documented in this file.

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