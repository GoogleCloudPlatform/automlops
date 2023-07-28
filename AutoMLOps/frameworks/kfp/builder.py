# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Builds KFP components and pipeline."""

# pylint: disable=line-too-long

import json

from typing import Dict, List, Optional
from AutoMLOps.utils.utils import (
    execute_process,
    get_components_list,
    make_dirs,
    read_yaml_file,
    is_using_kfp_spec,
    write_and_chmod,
    write_file,
    write_yaml_file
)
from AutoMLOps.utils.constants import (
    BASE_DIR,
    GENERATED_BUILD_COMPONENTS_SH_FILE,
    GENERATED_DEFAULTS_FILE,
    GENERATED_COMPONENT_BASE,
    GENERATED_PIPELINE_FILE,
    GENERATED_PIPELINE_SPEC_SH_FILE,
    GENERATED_RESOURCES_SH_FILE,
    GENERATED_RUN_PIPELINE_SH_FILE,
    GENERATED_RUN_ALL_SH_FILE,
    PIPELINE_CACHE_FILE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH
)
from AutoMLOps.frameworks.kfp.constructs.cloudrun import KfpCloudRun
from AutoMLOps.frameworks.kfp.constructs.component import KfpComponent
from AutoMLOps.frameworks.kfp.constructs.pipeline import KfpPipeline
from AutoMLOps.frameworks.kfp.constructs.scripts import KfpScripts

def build(project_id: str,
          pipeline_params: Dict,
          af_registry_location: Optional[str],
          af_registry_name: Optional[str],
          base_image: Optional[str],
          cb_trigger_location: Optional[str],
          cb_trigger_name: Optional[str],
          cloud_run_location: Optional[str],
          cloud_run_name: Optional[str],
          cloud_tasks_queue_location: Optional[str],
          cloud_tasks_queue_name: Optional[str],
          csr_branch_name: Optional[str],
          csr_name: Optional[str],
          custom_training_job_specs: Optional[List[Dict]],
          gs_bucket_location: Optional[str],
          gs_bucket_name: Optional[str],
          pipeline_runner_sa: Optional[str],
          run_local: Optional[bool],
          schedule_location: Optional[str],
          schedule_name: Optional[str],
          schedule_pattern: Optional[str],
          vpc_connector: Optional[str]):
    """Constructs scripts for resource deployment and running Kubeflow pipelines.

    Args:
        af_registry_location: Region of the Artifact Registry.
        af_registry_name: Artifact Registry name where components are stored.
        base_image: The image to use in the component base dockerfile.
        cb_trigger_location: The location of the cloudbuild trigger.
        cb_trigger_name: The name of the cloudbuild trigger.
        cloud_run_location: The location of the cloud runner service.
        cloud_run_name: The name of the cloud runner service.
        cloud_tasks_queue_location: The location of the cloud tasks queue.
        cloud_tasks_queue_name: The name of the cloud tasks queue.
        csr_branch_name: The name of the csr branch to push to to trigger cb job.
        csr_name: The name of the cloud source repo to use.
        gs_bucket_location: Region of the GS bucket.
        gs_bucket_name: GS bucket name where pipeline run metadata is stored.
        pipeline_runner_sa: Service Account to runner PipelineJobs.
        project_id: The project ID.
        run_local: Flag that determines whether to use Cloud Run CI/CD.
        schedule_location: The location of the scheduler resource.
        schedule_name: The name of the scheduler resource.
        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
        vpc_connector: The name of the vpc connector to use.
    """

    # Get scripts builder object
    kfp_scripts = KfpScripts(
        af_registry_location, af_registry_name, base_image, cb_trigger_location,
        cb_trigger_name, cloud_run_location, cloud_run_name,
        cloud_tasks_queue_location, cloud_tasks_queue_name, csr_branch_name,
        csr_name, gs_bucket_location, gs_bucket_name,
        pipeline_runner_sa, project_id, run_local, schedule_location,
        schedule_name, schedule_pattern, BASE_DIR, vpc_connector)

    # Write defaults.yaml
    write_file(GENERATED_DEFAULTS_FILE, kfp_scripts.defaults, 'w+')

    # Write scripts for building pipeline, building components, running pipeline, and running all files
    write_and_chmod(GENERATED_PIPELINE_SPEC_SH_FILE, kfp_scripts.build_pipeline_spec)
    write_and_chmod(GENERATED_BUILD_COMPONENTS_SH_FILE, kfp_scripts.build_components)
    write_and_chmod(GENERATED_RUN_PIPELINE_SH_FILE, kfp_scripts.run_pipeline)
    write_and_chmod(GENERATED_RUN_ALL_SH_FILE, kfp_scripts.run_all)

    # Write scripts to create resources
    write_and_chmod(GENERATED_RESOURCES_SH_FILE, kfp_scripts.create_resources_script)

    # Copy tmp pipeline file over to AutoMLOps directory
    execute_process(f'cp {PIPELINE_CACHE_FILE} {GENERATED_PIPELINE_FILE}', to_null=False)

    # Create components and pipelines
    components_path_list = get_components_list()
    for path in components_path_list:
        build_component(path)
    build_pipeline(custom_training_job_specs, pipeline_params)

    # Write empty .gitkeep to pipeline_spec directory
    write_file(f'{BASE_DIR}scripts/pipeline_spec/.gitkeep', '', 'w')

    # Write empty .gitkeep to pipeline_spec directory
    write_file(f'{BASE_DIR}README.md', kfp_scripts.readme, 'w')

    # Write dockerfile to the component base directory
    write_file(f'{GENERATED_COMPONENT_BASE}/Dockerfile', kfp_scripts.dockerfile, 'w')

    # Write requirements.txt to the component base directory
    write_file(f'{GENERATED_COMPONENT_BASE}/requirements.txt', kfp_scripts.requirements, 'w')

    # Build the cloud run files
    if not run_local:
        build_cloudrun()

def build_component(component_path: str):
    """Constructs and writes component.yaml and {component_name}.py files.
        component.yaml: Contains the Kubeflow custom component definition.
        {component_name}.py: Contains the python code from the Jupyter cell.

    Args:
        component_path: Path to the temporary component yaml. This file
            is used to create the permanent component.yaml, and deleted
            after calling AutoMLOps.generate().
    """
    # Read in component specs
    component_spec = read_yaml_file(component_path)

    # If using kfp, remove spaces in name and convert to lowercase
    if is_using_kfp_spec(component_spec['implementation']['container']['image']):
        component_spec['name'] = component_spec['name'].replace(' ', '_').lower()

    # Set and create directory for component, and set directory for task
    component_dir = BASE_DIR + 'components/' + component_spec['name']
    task_filepath = (BASE_DIR
                     + 'components/component_base/src/'
                     + component_spec['name']
                     + '.py')
    make_dirs([component_dir])

    # Initialize component scripts builder
    kfp_comp = KfpComponent(component_spec, GENERATED_DEFAULTS_FILE)

    # Write task script to component base
    write_file(task_filepath, kfp_comp.task, 'w+')

    # Update component_spec to include correct image and startup command
    component_spec['implementation']['container']['image'] = kfp_comp.compspec_image
    component_spec['implementation']['container']['command'] = [
        'python3',
        f'''/pipelines/component/src/{component_spec['name']+'.py'}''']

    # Write license and component spec to the appropriate component.yaml file
    filename = component_dir + '/component.yaml'
    write_file(filename, GENERATED_LICENSE, 'w')
    write_yaml_file(filename, component_spec, 'a')

def build_pipeline(custom_training_job_specs: List[Dict],
                   pipeline_parameter_values: dict):
    """Constructs and writes pipeline.py, pipeline_runner.py, and pipeline_parameter_values.json files.
        pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.

    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        pipeline_parameter_values: Dictionary of runtime parameters for the PipelineJob.
    Raises:
        Exception: If an error is encountered reading/writing to a file.
    """
    # Set paths
    pipeline_file = BASE_DIR + 'pipelines/pipeline.py'
    pipeline_runner_file = BASE_DIR + 'pipelines/pipeline_runner.py'
    pipeline_params_file = BASE_DIR + GENERATED_PARAMETER_VALUES_PATH

    # Initializes pipeline scripts builder
    kfp_pipeline = KfpPipeline(custom_training_job_specs, GENERATED_DEFAULTS_FILE)
    try:
        with open(pipeline_file, 'r+', encoding='utf-8') as file:
            pipeline_scaffold = file.read()
            file.seek(0, 0)
            file.write(GENERATED_LICENSE)
            file.write(kfp_pipeline.pipeline_imports)
            for line in pipeline_scaffold.splitlines():
                file.write('    ' + line + '\n')
            file.write(kfp_pipeline.pipeline_argparse)
        file.close()
    except OSError as err:
        raise OSError(f'Error interacting with file. {err}') from err

    # Construct pipeline_runner.py
    write_file(pipeline_runner_file, kfp_pipeline.pipeline_runner, 'w+')

    # Construct pipeline_parameter_values.json
    serialized_params = json.dumps(pipeline_parameter_values, indent=4)
    write_file(pipeline_params_file, serialized_params, 'w+')

def build_cloudrun():
    """Constructs and writes a Dockerfile, requirements.txt, and
       main.py to the cloud_run/run_pipeline directory. Also
       constructs and writes a main.py, requirements.txt, and
       pipeline_parameter_values.json to the
       cloud_run/queueing_svc directory.
    """
    # Make new directories
    make_dirs([BASE_DIR + 'cloud_run',
               BASE_DIR + 'cloud_run/run_pipeline',
               BASE_DIR + 'cloud_run/queueing_svc'])

    # Initialize cloud run scripts object
    cloudrun_scripts = KfpCloudRun(GENERATED_DEFAULTS_FILE)

    # Set new folders as variables
    cloudrun_base = BASE_DIR + 'cloud_run/run_pipeline'
    queueing_svc_base = BASE_DIR + 'cloud_run/queueing_svc'

    # Write cloud run dockerfile
    write_file(f'{cloudrun_base}/Dockerfile', cloudrun_scripts.dockerfile, 'w')

    # Write requirements files for cloud run base and queueing svc
    write_file(f'{cloudrun_base}/requirements.txt', cloudrun_scripts.cloudrun_base_reqs, 'w')
    write_file(f'{queueing_svc_base}/requirements.txt', cloudrun_scripts.queueing_svc_reqs, 'w')

    # Write main code files for cloud run base and queueing svc
    write_file(f'{cloudrun_base}/main.py', cloudrun_scripts.cloudrun_base, 'w')
    write_file(f'{queueing_svc_base}/main.py', cloudrun_scripts.queueing_svc, 'w')

    # Copy runtime parameters over to queueing_svc dir
    execute_process(f'''cp -r {BASE_DIR + GENERATED_PARAMETER_VALUES_PATH} {BASE_DIR + 'cloud_run/queueing_svc'}''', to_null=False)
