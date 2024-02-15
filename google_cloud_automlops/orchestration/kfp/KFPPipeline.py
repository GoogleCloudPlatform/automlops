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

"""Creates a KFP pipeline subclass."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

import json
import re
import textwrap
from typing import Callable, Optional

try:
    from importlib.resources import files as import_files
except ImportError:
    # Try backported to PY<37 `importlib_resources`
    from importlib_resources import files as import_files

from google_cloud_automlops.orchestration.Pipeline import Pipeline
from google_cloud_automlops.utils.utils import (
    execute_process,
    get_components_list,
    make_dirs,
    read_file,
    read_yaml_file,
    render_jinja,
    write_and_chmod,
    write_file,
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    GENERATED_BUILD_COMPONENTS_SH_FILE,
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


class KFPPipeline(Pipeline):
    """Creates a KFP specific Pipeline object for #TODO: add more

    Args:
        Pipeline (object): Generic Pipeline object.
    """

    def __init__(self,
                 func: Optional[Callable] = None,
                 *,
                 name: Optional[str] = None,
                 description: Optional[str] = None) -> None:
        """Initiates a KFP pipeline object created out of a function holding
        all necessary code.

        Args:
            func: The python function to create a pipeline from. The function
                should have type annotations for all its arguments, indicating how
                it is intended to be used (e.g. as an input/output Artifact object,
                a plain parameter, or a path to a file).
            name: The name of the pipeline.
            description: Short description of what the pipeline does.
        """
        super().__init__(
            func=func,
            name=name,
            description=description)

        # Create pipeline scaffold attribute # TODO: more descriptive
        self.pipeline_scaffold = (
            self._get_pipeline_decorator()
            + self.src_code
            + self._get_compile_step())

    def build(self,
              base_image,
              custom_training_job_specs,
              pipeline_params,
              pubsub_topic_name,
              use_ci):
        """Constructs files for running and managing Kubeflow pipelines.

            Files created under AutoMLOps/:
                README.md
                scripts/
                    pipeline_spec/.gitkeep
                    build_components.sh
                    build_pipeline_spec.sh
                    run_pipeline.sh
                    publish_to_topic.sh
                    run_all.sh
                components/
                    component_base/Dockerfile
                    component_base/requirements.txt
                pipelines/
                    pipeline.py
                    pipeline_runner.py
                    requirements.txt
                    runtime_parameters/pipeline_parameter_values.json
        """
        super().build(base_image,
                      custom_training_job_specs,
                      pipeline_params,
                      pubsub_topic_name,
                      use_ci)

        # Build necessary folders
        make_dirs([
            f'{BASE_DIR}scripts/pipeline_spec/',
            f'{BASE_DIR}pipelines',
            f'{BASE_DIR}pipelines/runtime_parameters/'
        ])

        # README.md: Write description of the contents of the directory
        write_file(
            filepath=f'{BASE_DIR}README.md', 
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH) / 'README.md.j2',
                use_ci=self.use_ci),
            mode='w')

        # components/component_base/dockerfile: Write the component base Dockerfile
        write_file(
            filepath=f'{GENERATED_COMPONENT_BASE}/Dockerfile',
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.components.component_base') / 'Dockerfile.j2',
                base_image=self.base_image,
                generated_license=GENERATED_LICENSE),
            mode='w')

        # components/component_base/requirements.txt: Write the component base requirements file
        write_file(
            filepath=f'{GENERATED_COMPONENT_BASE}/requirements.txt',
            text=self._create_component_base_requirements(),
            mode='w')

        # Save scripts template path
        scripts_template_path = import_files(KFP_TEMPLATES_PATH + '.scripts')

        # scripts/pipeline_spec/.gitkeep: Write gitkeep to pipeline_spec directory
        write_file(
            filepath=f'{BASE_DIR}scripts/pipeline_spec/.gitkeep',
            text='',
            mode='w')

        # scripts/build_components.sh: Write script for building components
        write_and_chmod(
            filepath=GENERATED_BUILD_COMPONENTS_SH_FILE,
            text=render_jinja(
                template_path=scripts_template_path / 'build_components.sh.j2',
                generated_license=GENERATED_LICENSE,
                base_dir=BASE_DIR))

        # scripts/build_pipeline_spec.sh: Write script for building pipeline specs
        write_and_chmod(
            filepath=GENERATED_PIPELINE_SPEC_SH_FILE,
            text=render_jinja(
                template_path=scripts_template_path / 'build_pipeline_spec.sh.j2',
                generated_license=GENERATED_LICENSE,
                base_dir=BASE_DIR))

        # scripts/run_pipline: Write script for running pipeline
        write_and_chmod(
            filepath=GENERATED_RUN_PIPELINE_SH_FILE,
            text=render_jinja(
                template_path=scripts_template_path / 'run_pipeline.sh.j2',
                generated_license=GENERATED_LICENSE,
                base_dir=BASE_DIR))

        # scripts/run_all.sh: Write script for running all files
        write_and_chmod(
            filepath=GENERATED_RUN_ALL_SH_FILE,
            text=render_jinja(
                template_path=scripts_template_path / 'run_all.sh.j2',
                generated_license=GENERATED_LICENSE,
                base_dir=BASE_DIR))

        # scripts/publish_to_topic.sh: If using CI, write script for publishing to pubsub topic
        if self.use_ci:
            write_and_chmod(
                filepath=GENERATED_PUBLISH_TO_TOPIC_FILE,
                text=render_jinja(
                    template_path=scripts_template_path / 'publish_to_topic.sh.j2',
                    base_dir=BASE_DIR,
                    generated_license=GENERATED_LICENSE,
                    generated_parameter_values_path=GENERATED_PARAMETER_VALUES_PATH,
                    pubsub_topic_name=self.pubsub_topic_name))

        # pipelines/pipeline.py: Generates a Kubeflow pipeline spec from custom components.
        components_list = get_components_list(full_path=False)
        pipeline_scaffold_contents = textwrap.indent(self.pipeline_scaffold, 4 * ' ')
        write_file(
            filepath=GENERATED_PIPELINE_FILE,
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'pipeline.py.j2',
                components_list=components_list,
                custom_training_job_specs=self.custom_training_job_specs,
                generated_license=GENERATED_LICENSE,
                pipeline_scaffold_contents=pipeline_scaffold_contents,
                project_id=self.project_id),
            mode='w')

        # pipelines/pipeline_runner.py: Sends a PipelineJob to Vertex AI using pipeline spec.
        write_file(
            filepath=GENERATED_PIPELINE_RUNNER_FILE,
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'pipeline_runner.py.j2',
                generated_license=GENERATED_LICENSE),
            mode='w')

        # pipelines/requirements.txt
        write_file(
            filepath=GENERATED_PIPELINE_REQUIREMENTS_FILE,
            text=render_jinja(
                template_path=import_files(KFP_TEMPLATES_PATH + '.pipelines') / 'requirements.txt.j2',
                pinned_kfp_version=PINNED_KFP_VERSION),
            mode='w')

        # pipelines/runtime_parameters/pipeline_parameter_values.json: Provides runtime parameters for the PipelineJob.
        self.pipeline_params['gs_pipeline_spec_path'] = self.gs_pipeline_job_spec_path
        serialized_params = json.dumps(self.pipeline_params, indent=4)
        write_file(BASE_DIR + GENERATED_PARAMETER_VALUES_PATH, serialized_params, 'w')

    def _get_pipeline_decorator(self):
        """Creates the kfp pipeline decorator.

        Args:
            name: The name of the pipeline.
            description: Short description of what the pipeline does.

        Returns:
            str: Python compile function call.
        """
        name_str = f'''(\n    name='{self.name}',\n'''
        desc_str = f'''    description='{self.description}',\n''' if self.description else ''
        ending_str = ')\n'
        return '@dsl.pipeline' + name_str + desc_str + ending_str

    def _get_compile_step(self):
        """Creates the compile function call.

        Args:
            func_name: The name of the pipeline function.

        Returns:
            str: Python compile function call.
        """
        return (
            f'\n'
            f'compiler.Compiler().compile(\n'
            f'    pipeline_func={self.func_name},\n'
            f'    package_path=pipeline_job_spec_path)\n'
            f'\n'
        )

    def _create_component_base_requirements(self):
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
