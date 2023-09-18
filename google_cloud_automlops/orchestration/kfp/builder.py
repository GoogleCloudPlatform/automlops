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
try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files
import re
import textwrap

from jinja2 import Template

from google_cloud_automlops.utils.utils import (
    execute_process,
    get_components_list,
    make_dirs,
    read_file,
    read_yaml_file,
    is_using_kfp_spec,
    write_and_chmod,
    write_file,
    write_yaml_file
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_BUILD_COMPONENTS_SH_FILE,
    GENERATED_DEFAULTS_FILE,
    GENERATED_COMPONENT_BASE,
    GENERATED_LICENSE,
    GENERATED_PARAMETER_VALUES_PATH,
    GENERATED_PIPELINE_FILE,
    GENERATED_PIPELINE_REQUIREMENTS_FILE,
    GENERATED_PIPELINE_RUNNER_FILE,
    GENERATED_PIPELINE_SPEC_SH_FILE,
    GENERATED_PUBLISH_TO_TOPIC_FILE,
    GENERATED_RUN_PIPELINE_SH_FILE,
    GENERATED_RUN_ALL_SH_FILE,
    KFP_TEMPLATES_PATH,
    PINNED_KFP_VERSION,
    PIPELINE_CACHE_FILE
)
from google_cloud_automlops.orchestration.configs import KfpConfig

def build(config: KfpConfig):
    """Constructs files for running and managing Kubeflow pipelines.

    Args:
        config.base_image: The image to use in the component base dockerfile.
        config.custom_training_job_specs: Specifies the specs to run the training job with.
        config.pipeline_params: Dictionary containing runtime pipeline parameters.
        config.pubsub_topic_name: The name of the pubsub topic to publish to.
        config.use_ci: Flag that determines whether to use Cloud Run CI/CD.
    """

    # Write scripts for building pipeline, building components, running pipeline, and running all files
    write_and_chmod(GENERATED_PIPELINE_SPEC_SH_FILE, build_pipeline_spec_jinja())
    write_and_chmod(GENERATED_BUILD_COMPONENTS_SH_FILE, build_components_jinja())
    write_and_chmod(GENERATED_RUN_PIPELINE_SH_FILE, run_pipeline_jinja())
    write_and_chmod(GENERATED_RUN_ALL_SH_FILE, run_all_jinja())
    if config.use_ci:
        write_and_chmod(GENERATED_PUBLISH_TO_TOPIC_FILE, publish_to_topic_jinja(pubsub_topic_name=config.pubsub_topic_name))

    # Create components and pipelines
    components_path_list = get_components_list(full_path=True)
    for path in components_path_list:
        build_component(path)
    build_pipeline(config.custom_training_job_specs, config.pipeline_params)

    # Write empty .gitkeep to pipeline_spec directory
    write_file(f'{BASE_DIR}scripts/pipeline_spec/.gitkeep', '', 'w')

    # Write readme.md to description the contents of the directory
    write_file(f'{BASE_DIR}README.md', readme_jinja(config.use_ci), 'w')

    # Write dockerfile to the component base directory
    write_file(f'{GENERATED_COMPONENT_BASE}/Dockerfile', component_base_dockerfile_jinja(config.base_image), 'w')

    # Write requirements.txt to the component base directory
    write_file(f'{GENERATED_COMPONENT_BASE}/requirements.txt', create_component_base_requirements(), 'w')

    # Build the submission service files
    if config.use_ci:
        build_services()


def build_component(component_path: str):
    """Constructs and writes component.yaml and {component_name}.py files.
        component.yaml: Contains the Kubeflow custom component definition.
        {component_name}.py: Contains the python code from the Jupyter cell.

    Args:
        component_path: Path to the temporary component yaml. This file
            is used to create the permanent component.yaml, and deleted
            after calling AutoMLOps.generate().
    """
    # Retrieve defaults vars
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)

    # Read in component specs
    component_spec = read_yaml_file(component_path)
    kfp_spec_bool = is_using_kfp_spec(component_spec['implementation']['container']['image'])
    custom_code_contents = component_spec['implementation']['container']['command'][-1]
    compspec_image = (
            f'''{defaults['gcp']['artifact_repo_location']}-docker.pkg.dev/'''
            f'''{defaults['gcp']['project_id']}/'''
            f'''{defaults['gcp']['artifact_repo_name']}/'''
            f'''{defaults['gcp']['naming_prefix']}/'''
            f'''components/component_base:latest''')

    # If using kfp, remove spaces in name and convert to lowercase
    if kfp_spec_bool:
        component_spec['name'] = component_spec['name'].replace(' ', '_').lower()

    # Set and create directory for component, and set directory for task
    component_dir = BASE_DIR + 'components/' + component_spec['name']
    make_dirs([component_dir])
    task_filepath = (BASE_DIR
                     + 'components/component_base/src/'
                     + component_spec['name']
                     + '.py')

    # Write task script to component base
    write_file(task_filepath, component_base_task_file_jinja(custom_code_contents, kfp_spec_bool), 'w')

    # Update component_spec to include correct image and startup command
    component_spec['implementation']['container']['image'] = compspec_image
    component_spec['implementation']['container']['command'] = [
        'python3',
        f'''/pipelines/component/src/{component_spec['name']+'.py'}''']

    # Write license and component spec to the appropriate component.yaml file
    filename = component_dir + '/component.yaml'
    write_file(filename, GENERATED_LICENSE, 'w')
    write_yaml_file(filename, component_spec, 'a')


def build_pipeline(custom_training_job_specs: list,
                   pipeline_parameter_values: dict):
    """Constructs and writes pipeline.py, pipeline_runner.py, and pipeline_parameter_values.json files.
        pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.

    Args:
        custom_training_job_specs: Specifies the specs to run the training job with.
        pipeline_parameter_values: Dictionary of runtime parameters for the PipelineJob.
    """
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    # Get the names of the components
    components_list = get_components_list(full_path=False)
    # Read pipeline definition
    pipeline_scaffold_contents = read_file(PIPELINE_CACHE_FILE)
    # Add indentation
    pipeline_scaffold_contents = textwrap.indent(pipeline_scaffold_contents, 4 * ' ')
    # Construct pipeline.py
    project_id = defaults['gcp']['project_id']
    write_file(GENERATED_PIPELINE_FILE, pipeline_jinja(
        components_list,
        custom_training_job_specs,
        pipeline_scaffold_contents,
        project_id=project_id), 'w')
    # Construct pipeline_runner.py
    write_file(GENERATED_PIPELINE_RUNNER_FILE, pipeline_runner_jinja(), 'w')
    # Construct requirements.txt
    write_file(GENERATED_PIPELINE_REQUIREMENTS_FILE, pipeline_requirements_jinja(), 'w')
    # Add pipeline_spec_path to dict
    pipeline_parameter_values['gs_pipeline_spec_path'] = defaults['pipelines']['gs_pipeline_job_spec_path']
    # Construct pipeline_parameter_values.json
    serialized_params = json.dumps(pipeline_parameter_values, indent=4)
    write_file(BASE_DIR + GENERATED_PARAMETER_VALUES_PATH, serialized_params, 'w')


def build_services():
    """Constructs and writes a Dockerfile, requirements.txt, and
       main.py to the services/submission_service directory.
    """
    # Retrieve defaults vars
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)

    # Set new folders as variables
    submission_service_base = BASE_DIR + 'services/submission_service'

    # Write cloud run dockerfile
    write_file(f'{submission_service_base}/Dockerfile', submission_service_dockerfile_jinja(), 'w')

    # Write requirements files for cloud run base and queueing svc
    write_file(f'{submission_service_base}/requirements.txt', submission_service_requirements_jinja(
        pipeline_job_submission_service_type=defaults['gcp']['pipeline_job_submission_service_type']), 'w')

    # Write main code files for cloud run base and queueing svc
    write_file(f'{submission_service_base}/main.py', submission_service_main_jinja(
                    pipeline_root=defaults['pipelines']['pipeline_storage_path'],
                    pipeline_job_runner_service_account=defaults['gcp']['pipeline_job_runner_service_account'],
                    pipeline_job_submission_service_type=defaults['gcp']['pipeline_job_submission_service_type'],
                    project_id=defaults['gcp']['project_id']), 'w')


def create_component_base_requirements():
    """Writes a requirements.txt to the component_base directory.
    Infers pip requirements from the python srcfiles using 
    pipreqs. Takes user-inputted requirements, and addes some 
    default gcp packages as well as packages that are often missing
    in setup.py files (e.g db_types, pyarrow, gcsfs, fsspec).
    """
    reqs_filename = f'{GENERATED_COMPONENT_BASE}/requirements.txt'
    default_gcp_reqs = [
        'google-cloud-aiplatform',
        'google-cloud-appengine-logging',
        'google-cloud-audit-log',
        'google-cloud-bigquery',
        'google-cloud-bigquery-storage',
        'google-cloud-bigtable',
        'google-cloud-core',
        'google-cloud-dataproc',
        'google-cloud-datastore',
        'google-cloud-dlp',
        'google-cloud-firestore',
        'google-cloud-kms',
        'google-cloud-language',
        'google-cloud-logging',
        'google-cloud-monitoring',
        'google-cloud-notebooks',
        'google-cloud-pipeline-components',
        'google-cloud-pubsub',
        'google-cloud-pubsublite',
        'google-cloud-recommendations-ai',
        'google-cloud-resource-manager',
        'google-cloud-scheduler',
        'google-cloud-spanner',
        'google-cloud-speech',
        'google-cloud-storage',
        'google-cloud-tasks',
        'google-cloud-translate',
        'google-cloud-videointelligence',
        'google-cloud-vision',
        'db_dtypes',
        'pyarrow',
        'gcsfs',
        'fsspec']
    # Get user-inputted requirements from the cache dir
    user_inp_reqs = []
    components_path_list = get_components_list()
    for component_path in components_path_list:
        component_spec = read_yaml_file(component_path)
        reqs = component_spec['implementation']['container']['command'][2]
        formatted_reqs = re.findall('\'([^\']*)\'', reqs)
        user_inp_reqs.extend(formatted_reqs)
    # Check if user inputted requirements
    if user_inp_reqs:
        # Remove duplicates
        set_of_requirements = set(user_inp_reqs)
    else:
        # If user did not input requirements, then infer reqs using pipreqs
        execute_process(f'python3 -m pipreqs.pipreqs {GENERATED_COMPONENT_BASE} --mode no-pin --force', to_null=True)
        pipreqs = read_file(reqs_filename).splitlines()
        set_of_requirements = set(pipreqs + default_gcp_reqs)
    # Remove empty string
    if '' in set_of_requirements:
        set_of_requirements.remove('')
    # Pin kfp version
    if 'kfp' in set_of_requirements:
        set_of_requirements.remove('kfp')
    set_of_requirements.add(PINNED_KFP_VERSION)
    # Stringify and sort
    reqs_str = ''.join(r+'\n' for r in sorted(set_of_requirements))
    return reqs_str


def build_pipeline_spec_jinja() -> str:
    """Generates code for build_pipeline_spec.sh which builds the pipeline specs.

    Returns:
        str: build_pipeline_spec.sh script.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.scripts') / 'build_pipeline_spec.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            base_dir=BASE_DIR)


def build_components_jinja() -> str:
    """Generates code for build_components.sh which builds the components.

    Returns:
        str: build_components.sh script.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.scripts') / 'build_components.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            base_dir=BASE_DIR)


def run_pipeline_jinja() -> str:
    """Generates code for run_pipeline.sh which runs the pipeline locally.

    Returns:
        str: run_pipeline.sh script.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.scripts') / 'run_pipeline.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            base_dir=BASE_DIR)


def run_all_jinja() -> str:
    """Generates code for run_all.sh which builds runs all other shell scripts.

    Returns:
        str: run_all.sh script.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.scripts') / 'run_all.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            base_dir=BASE_DIR)


def publish_to_topic_jinja(pubsub_topic_name: str) -> str:
    """Generates code for publish_to_topic.sh which submits a message to the
       pipeline job submission service.

    Args:
        pubsub_topic_name: The name of the pubsub topic to publish to.

    Returns:
        str: publish_to_topic.sh script.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.scripts') / 'publish_to_topic.sh.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            base_dir=BASE_DIR,
            generated_license=GENERATED_LICENSE,
            generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
            pubsub_topic_name=pubsub_topic_name)


def readme_jinja(use_ci: str) -> str:
    """Generates code for readme.md which is a readme markdown file to describe the contents of the
        generated AutoMLOps code repo.

    Args:
        use_ci: Flag that determines whether to use Cloud CI/CD.

    Returns:
        str: README.md file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH) / 'README.md.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(use_ci=use_ci)


def component_base_dockerfile_jinja(base_image: str) -> str:
    """Generates code for a Dockerfile to be written to the component_base directory.

    Args:
        base_image: The image to use in the component base dockerfile.

    Returns:
        str: Dockerfile file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.components.component_base') / 'Dockerfile.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            base_image=base_image,
            generated_license=GENERATED_LICENSE)


def component_base_task_file_jinja(custom_code_contents: str, kfp_spec_bool: str) -> str:
    """Generates code for the task.py file to be written to the component_base/src directory.

    Args:
        custom_code_contents: Code inside of the component, specified by the user.
        kfp_spec_bool: Boolean that specifies whether components are defined using kfp.

    Returns:
        str: Contents of the task.py file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.components.component_base.src') / 'task.py.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            custom_code_contents=custom_code_contents,
            generated_license=GENERATED_LICENSE,
            kfp_spec_bool=kfp_spec_bool)


def pipeline_runner_jinja() -> str:
    """Generates code for the pipeline_runner.py file to be written to the pipelines directory.

    Returns:
        str: pipeline_runner.py file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'pipeline_runner.py.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(generated_license=GENERATED_LICENSE)


def pipeline_jinja(
    components_list: list,
    custom_training_job_specs: list,
    pipeline_scaffold_contents: str,
    project_id: str) -> str:
    """Generates code for the pipeline.py file to be written to the pipelines directory.

    Args:
        components_list: Contains the names or paths of all component yamls in the dir.
        custom_training_job_specs: Specifies the specs to run the training job with.
        pipeline_scaffold_contents: The contents of the pipeline scaffold file,
            which can be found at PIPELINE_CACHE_FILE.
        project_id: The project ID.
    
    Returns:
        str: pipeline.py file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'pipeline.py.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            components_list=components_list,
            custom_training_job_specs=custom_training_job_specs,
            generated_license=GENERATED_LICENSE,
            pipeline_scaffold_contents=pipeline_scaffold_contents,
            project_id=project_id)


def pipeline_requirements_jinja() -> str:
    """Generates code for a requirements.txt to be written to the pipelines directory.

    Returns:
        str: requirements.txt file for pipelines.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'requirements.txt.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(pinned_kfp_version=PINNED_KFP_VERSION)


def submission_service_dockerfile_jinja() -> str:
    """Generates code for a Dockerfile to be written to the serivces/submission_service directory.

    Returns:
        str: Dockerfile file.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'Dockerfile.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            base_dir=BASE_DIR,
            generated_license=GENERATED_LICENSE)


def submission_service_requirements_jinja(pipeline_job_submission_service_type: str) -> str:
    """Generates code for a requirements.txt to be written to the serivces/submission_service directory.
    
    Args:
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).

    Returns:
        str: requirements.txt file for submission_service.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'requirements.txt.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            pinned_kfp_version=PINNED_KFP_VERSION,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type)


def submission_service_main_jinja(
    pipeline_root: str,
    pipeline_job_runner_service_account: str,
    pipeline_job_submission_service_type: str,
    project_id: str) -> str:
    """Generates content for main.py to be written to the serivces/submission_service directory. 
       This file contains code for running a flask service that will act as a pipeline job submission service.

    Args:
        pipeline_root: GS location where to store metadata from pipeline runs.
        pipeline_job_runner_service_account: Service Account to runner PipelineJobs.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        project_id: The project ID.

    Returns:
        str: Content of serivces/submission_service main.py.
    """
    template_file = import_files(KFP_TEMPLATES_PATH + '.services.submission_service') / 'main.py.j2'
    with template_file.open('r', encoding='utf-8') as f:
        template = Template(f.read())
        return template.render(
            generated_license=GENERATED_LICENSE,
            pipeline_root=pipeline_root,
            pipeline_job_runner_service_account=pipeline_job_runner_service_account,
            pipeline_job_submission_service_type=pipeline_job_submission_service_type,
            project_id=project_id)
