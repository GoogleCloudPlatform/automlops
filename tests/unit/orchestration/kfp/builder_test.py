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

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import json
import os
from typing import List

import pytest
import pytest_mock

from google_cloud_automlops.utils.constants import (
    GENERATED_LICENSE,
    PINNED_KFP_VERSION
)
import google_cloud_automlops.orchestration.kfp.builder
from google_cloud_automlops.orchestration.kfp.builder import (
    build_component,
    build_pipeline,
    build_services,
    build_pipeline_spec_jinja,
    build_components_jinja,
    run_pipeline_jinja,
    run_all_jinja,
    publish_to_topic_jinja,
    readme_jinja,
    component_base_dockerfile_jinja,
    component_base_task_file_jinja,
    pipeline_runner_jinja,
    pipeline_jinja,
    pipeline_requirements_jinja,
    submission_service_dockerfile_jinja,
    submission_service_requirements_jinja,
    submission_service_main_jinja
)
import google_cloud_automlops.utils.utils
from google_cloud_automlops.utils.utils import (
    make_dirs,
    read_yaml_file,
    write_yaml_file
)

DEFAULTS = {
    'gcp': {
        'artifact_repo_location': 'us-central1',
        'project_id': 'my_project',
        'artifact_repo_name': 'my_af_registry',
        'naming_prefix': 'my-prefix',
        'pipeline_job_runner_service_account': 'my-service-account@service.com',
        'pipeline_job_submission_service_type': 'cloud-functions'
    },
    'pipelines': {
        'gs_pipeline_job_spec_path': 'gs://my-bucket/pipeline_root/my-prefix/pipeline_job.json',
        'pipeline_storage_path': 'gs://my-bucket/pipeline_root/'
    }
}

TEMP_YAML = {
    'name': 'create_dataset',
    'description': 'Custom component that takes in a BQ table and writes it to GCS.',
    'inputs': [
        {
            'name': 'bq_table',
            'description': 'The source biquery table.',
            'type': 'String',
        },
        {
            'name': 'data_path',
            'description': 'The gcs location to write the csv.',
            'type': 'String',
        },
        {
            'name': 'project_id',
            'description': 'The project ID.',
            'type': 'String'},
    ],
    'implementation': {
        'container': {
            'image': 'TBD',
            'command': [
                'sh',
                '-c',
                'if ! [ -x "$(command -v pip)" ]; then\n    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip\nfi\nPIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet \\\n    --no-warn-script-location  && "$0" "$@"\n\n',
                'def create_dataset(\n    bq_table: str,\n    data_path: str,\n    project_id: str\n):\n    """Custom component that takes in a BQ table and writes it to GCS.\n\n    Args:\n        bq_table: The source biquery table.\n        data_path: The gcs location to write the csv.\n        project_id: The project ID.\n    """\n    from google.cloud import bigquery\n    import pandas as pd\n    from sklearn import preprocessing\n\n    bq_client = bigquery.Client(project=project_id)\n\n    def get_query(bq_input_table: str) -> str:\n        """Generates BQ Query to read data.\n\n        Args:\n        bq_input_table: The full name of the bq input table to be read into\n        the dataframe (e.g. <project>.<dataset>.<table>)\n        Returns: A BQ query string.\n        """\n        return f\'\'\'\n        SELECT *\n        FROM `{bq_input_table}`\n        \'\'\'\n\n    def load_bq_data(query: str, client: bigquery.Client) -> pd.DataFrame:\n        """Loads data from bq into a Pandas Dataframe for EDA.\n        Args:\n        query: BQ Query to generate data.\n        client: BQ Client used to execute query.\n        Returns:\n        pd.DataFrame: A dataframe with the requested data.\n        """\n        df = client.query(query).to_dataframe()\n        return df\n\n    dataframe = load_bq_data(get_query(bq_table), bq_client)\n    le = preprocessing.LabelEncoder()\n    dataframe[\'Class\'] = le.fit_transform(dataframe[\'Class\'])\n    dataframe.to_csv(data_path, index=False)\n',
            ],
            'args': [
                '--executor_input',
                {'executorInput': None},
                '--function_to_execute',
                'create_dataset',
            ],
        }
    },
}


@pytest.fixture(name='temp_yaml_dict', params=[TEMP_YAML])
def fixture_temp_yaml_dict(request: pytest.FixtureRequest, tmpdir: pytest.FixtureRequest):
    """Writes temporary yaml file fixture using defaults parameterized
    dictionaries during pytest session scope.

    Args:
        request: Pytest fixture special object that provides information
            about the fixture.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """
    yaml_path = tmpdir.join('test.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}


@pytest.fixture(name='defaults_dict', params=[DEFAULTS])
def fixture_defaults_dict(request: pytest.FixtureRequest, tmpdir: pytest.FixtureRequest):
    """Writes temporary yaml file fixture using defaults parameterized
    dictionaries during pytest session scope.

    Args:
        request: Pytest fixture special object that provides information
            about the fixture.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.

    Returns:
        dict: Path of yaml file and dictionary it contains.
    """
    yaml_path = tmpdir.join('defaults.yaml')
    write_yaml_file(yaml_path, request.param, 'w')
    return {'path': yaml_path, 'vals': request.param}


@pytest.fixture(name='expected_component_dict')
def fixture_expected_component_dict():
    """Creates the expected component dictionary, which is the temporary yaml
    file with a change to the implementation key.

    Returns:
        dict: Expected component dictionary generated from the component
            builder.
    """
    expected = TEMP_YAML
    expected['implementation'] = {
        'container': {
            'image': 'us-central1-docker.pkg.dev/my_project/my_af_registry/my-prefix/components/component_base:latest',
            'command': ['python3', '/pipelines/component/src/create_dataset.py'],
            'args': [
                '--executor_input',
                {'executorInput': None},
                '--function_to_execute',
                'create_dataset',
            ],
        }
    }
    return expected


def test_build_component(mocker: pytest_mock.MockerFixture,
                         tmpdir: pytest.FixtureRequest,
                         temp_yaml_dict: pytest.FixtureRequest,
                         defaults_dict: pytest.FixtureRequest,
                         expected_component_dict: pytest.FixtureRequest):
    """Tests build_component, which Constructs and writes component.yaml and
    {component_name}.py files.

    Args:
        mocker: Mocker to patch directories.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.
        temp_yaml_dict: Locally defined temp_yaml_file Pytest fixture.
        defaults_dict: Locally defined defaults_dict Pytest fixture.
        expected_component_dict: Locally defined expected_component_dict
            Pytest fixture.
    """
    # Patch filepath constants to point to test path.
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'BASE_DIR', 
                        f'{tmpdir}/')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_DEFAULTS_FILE',
                        defaults_dict['path'])

    # Extract component name, create required directories, run build_component
    component_name = TEMP_YAML['name']
    make_dirs([f'{tmpdir}/components/component_base/src'])
    build_component(temp_yaml_dict['path'])

    # Ensure correct files are created with build_component call
    assert os.path.exists(f'{tmpdir}/components/{component_name}/component.yaml')
    assert os.path.exists(f'{tmpdir}/components/component_base/src/{component_name}.py')

    # Load component.yaml file and compare to the expected output in test_data
    created_component_dict = read_yaml_file(f'{tmpdir}/components/{component_name}/component.yaml')
    assert created_component_dict == expected_component_dict


@pytest.mark.parametrize(
    'custom_training_job_specs, pipeline_parameter_values',
    [
        (
            [{'component_spec': 'mycomp1', 'other': 'myother'}],
            {
                'bq_table': 'automlops-sandbox.test_dataset.dry-beans',
                'model_directory': 'gs://automlops-sandbox-bucket/trained_models/2023-05-31 13:00:41.379753',
                'data_path': 'gs://automlops-sandbox-bucket/data.csv',
                'project_id': 'automlops-sandbox',
                'region': 'us-central1'
            },
        ),
        (
            [
                {
                    'component_spec': 'train_model',
                    'display_name': 'train-model-accelerated',
                    'machine_type': 'a2-highgpu-1g',
                    'accelerator_type': 'NVIDIA_TESLA_A100',
                    'accelerator_count': '1',
                }
            ],
            {
                'bq_table': 'automlops-sandbox.test_dataset.dry-beans',
                'model_directory': 'gs://automlops-sandbox-bucket/trained_models/2023-05-31 13:00:41.379753',
                'data_path': 'gs://automlops-sandbox-bucket/data.csv',
                'project_id': 'automlops-sandbox',
                'region': 'us-central1'
            },
        ),
        (
            [
                {
                    'component_spec': 'test_model',
                    'display_name': 'test-model-accelerated',
                    'machine_type': 'a2-highgpu-1g',
                    'accelerator_type': 'NVIDIA_TESLA_A100',
                    'accelerator_count': '1',
                }
            ],
            {
                'bq_table': 'automlops-sandbox.test_dataset.dry-beans2',
                'model_directory': 'gs://automlops-sandbox-bucket/trained_models/2023-05-31 14:00:41.379753',
                'data_path': 'gs://automlops-sandbox-bucket/data2.csv',
                'project_id': 'automlops-sandbox',
                'region': 'us-central1'
            },
        )
    ]
)
def test_build_pipeline(mocker: pytest_mock.MockerFixture,
                        tmpdir: pytest.FixtureRequest,
                        defaults_dict: pytest.FixtureRequest,
                        custom_training_job_specs: List[dict],
                        pipeline_parameter_values: dict):
    """Tests build_pipeline, which constructs and writes pipeline.py,
    pipeline_runner.py, and pipeline_parameter_values.json files.

    Args:
        mocker: Mocker to patch directories.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.
        defaults_dict: Locally defined defaults_dict Pytest fixture.
        custom_training_job_specs (List[dict]): Specifies the specs to run the training job with.
        pipeline_parameter_values (dict): Dictionary of runtime parameters for the PipelineJob.
    """
    # Patch constants and other functions
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'BASE_DIR',
                        f'{tmpdir}/')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_DEFAULTS_FILE',
                        defaults_dict['path'])
    mocker.patch.object(google_cloud_automlops.utils.utils,
                        'CACHE_DIR',
                        f'{tmpdir}/.AutoMLOps-cache')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'PIPELINE_CACHE_FILE',
                        f'{tmpdir}/.AutoMLOps-cache/pipeline_scaffold.py')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_PIPELINE_FILE',
                        f'{tmpdir}/pipelines/pipeline.py')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_PIPELINE_RUNNER_FILE',
                        f'{tmpdir}/pipelines/pipeline_runner.py')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_PIPELINE_REQUIREMENTS_FILE',
                        f'{tmpdir}/pipelines/requirements.txt')

    # Create required directory and file for build_pipeline
    make_dirs([f'{tmpdir}/pipelines/runtime_parameters', f'{tmpdir}/.AutoMLOps-cache'])
    os.system(f'touch {tmpdir}/.AutoMLOps-cache/pipeline_scaffold.py')
    build_pipeline(custom_training_job_specs, pipeline_parameter_values)

    # Ensure correct files were created
    assert os.path.exists(f'{tmpdir}/pipelines/pipeline.py')
    assert os.path.exists(f'{tmpdir}/pipelines/pipeline_runner.py')
    assert os.path.exists(f'{tmpdir}/pipelines/requirements.txt')
    assert os.path.exists(f'{tmpdir}/pipelines/runtime_parameters/pipeline_parameter_values.json')

    # Ensure pipeline_parameter_values.json was created as expected
    with open(f'{tmpdir}/pipelines/runtime_parameters/pipeline_parameter_values.json', mode='r', encoding='utf-8') as f:
        pipeline_params_dict = json.load(f)
    assert pipeline_params_dict == pipeline_parameter_values


def test_build_services(mocker: pytest_mock.MockerFixture,
                        tmpdir: pytest.FixtureRequest,
                        defaults_dict: pytest.FixtureRequest):
    """Tests build_services, which Constructs and writes a Dockerfile, requirements.txt, and
       main.py to the services/submission_service directory.

    Args:
        mocker: Mocker to patch directories.
        tmpdir: Pytest fixture that provides a temporary directory unique
            to the test invocation.
        defaults_dict: Locally defined defaults_dict Pytest fixture.
    """
    # Patch filepath constants to point to test path.
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'BASE_DIR', 
                        f'{tmpdir}/')
    mocker.patch.object(google_cloud_automlops.orchestration.kfp.builder,
                        'GENERATED_DEFAULTS_FILE',
                        defaults_dict['path'])

    # create required directories, run build_services
    make_dirs([f'{tmpdir}/services/submission_service'])
    build_services()

    # Ensure correct files are created with build_services call
    assert os.path.exists(f'{tmpdir}/services/submission_service/Dockerfile')
    assert os.path.exists(f'{tmpdir}/services/submission_service/requirements.txt')
    assert os.path.exists(f'{tmpdir}/services/submission_service/main.py')


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, 'python3 -m pipelines.pipeline --config $CONFIG_FILE'])]
)
def test_build_pipeline_spec_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests build_pipeline_spec_jinja, which generates code for build_pipeline_spec.sh 
       which builds the pipeline specs. There is one test case for this function:
        1. Checks for the apache license and the pipeline compile command.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    build_pipeline_spec_script = build_pipeline_spec_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in build_pipeline_spec_script
        elif not is_included:
            assert snippet not in build_pipeline_spec_script


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, 'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600'])]
)
def test_build_components_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests build_components_jinja, which generates code for build_components.sh
       which builds the components. There is one test case for this function:
        1. Checks for the apache license and the builds submit command.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    build_components_script = build_components_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in build_components_script
        elif not is_included:
            assert snippet not in build_components_script


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, 'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE'])]
)
def test_run_pipeline_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests run_pipeline_jinja, which generates code for run_pipeline.sh
       which runs the pipeline locally. There is one test case for this function:
        1. Checks for the apache license and the pipeline runner command.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    run_pipeline_script = run_pipeline_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in run_pipeline_script
        elif not is_included:
            assert snippet not in run_pipeline_script


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, 'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600',
             './scripts/build_pipeline_spec.sh', './scripts/run_pipeline.sh'])]
)
def test_run_all_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests run_all_jinja, which generates code for run_all.sh
       which builds runs all other shell scripts. There is one test case for this function:
        1. Checks for the apache license and the builds submit, the pipeline compile, and the pipeline runner commands.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    run_all_script = run_all_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in run_all_script
        elif not is_included:
            assert snippet not in run_all_script


@pytest.mark.parametrize(
    'pubsub_topic_name, is_included, expected_output_snippets',
    [('my-topic', True, [GENERATED_LICENSE, 'gcloud pubsub topics publish my-topic'])]
)
def test_publish_to_topic_jinja(
    pubsub_topic_name: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests publish_to_topic_jinja, which generates code for publish_to_topic.sh 
       which submits a message to the pipeline job submission service.
       There is one test case for this function:
        1. Checks for the apache license and the pubsub publish command.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    publish_to_topic_script = publish_to_topic_jinja(pubsub_topic_name=pubsub_topic_name)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in publish_to_topic_script
        elif not is_included:
            assert snippet not in publish_to_topic_script


@pytest.mark.parametrize(
    'use_ci, is_included, expected_output_snippets',
    [
        (
            True, True,
            ['AutoMLOps - Generated Code Directory',
             '├── components',
             '├── configs',
             '├── images',
             '├── provision',
             '├── scripts',
             '├── services',
             '├── README.md',
             '└── cloudbuild.yaml']
        ),
        (
            False, False,
            ['├── publish_to_topic.sh'
             '├── services']
        ),
    ]
)
def test_readme_jinja(
    use_ci: bool,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests readme_jinja, which generates code for readme.md which
       is a readme markdown file to describe the contents of the
       generated AutoMLOps code repo. There are two test cases for this function:
        1. Checks that certain directories and files exist when use_ci=True.
        2. Checks that certain directories and files do not exist when use_ci=False.

    Args:
        use_ci: Flag that determines whether to use Cloud CI/CD.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    readme_str = readme_jinja(use_ci=use_ci)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in readme_str
        elif not is_included:
            assert snippet not in readme_str


@pytest.mark.parametrize(
    'base_image, is_included, expected_output_snippets',
    [('my-base-image', True, [GENERATED_LICENSE, 'FROM my-base-image'])]
)
def test_component_base_dockerfile_jinja(
    base_image: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests readme_jinja, which generates code for a Dockerfile 
       to be written to the component_base directory. There is one 
       test case for this function:
        1. Checks for the apache license and the FROM image line.

    Args:
        base_image: The image to use in the component base dockerfile.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    component_base_dockerfile = component_base_dockerfile_jinja(base_image)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in component_base_dockerfile
        elif not is_included:
            assert snippet not in component_base_dockerfile


@pytest.mark.parametrize(
    'custom_code_contents, kfp_spec_bool, is_included, expected_output_snippets',
    [
        (
            'this is some custom code', True, True,
            [GENERATED_LICENSE,
             'this is some custom code',
             'def main():']
        ),
        (
            'this is some custom code', False, True,
            [GENERATED_LICENSE,
             'this is some custom code',
             'def main():',
             'import kfp',
             'from kfp.v2.dsl import *']
        ),
        (
            'this is some custom code', True, False,
            ['import kfp',
             'from kfp.v2.dsl import *']
        )
    ]
)
def test_component_base_task_file_jinja(
    custom_code_contents: str,
    kfp_spec_bool: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests component_base_task_file_jinja, which generates code 
       for the task.py file to be written to the component_base/src directory.
       There are three test cases for this function:
        1. Checks for the apache license, the custom_code_contents, and a main function when using kfp spec (kfp spec comes with kfp imports by default).
        2. Checks for the apache license, the custom_code_contents, a main function, and kfp imports when not using kfp spec.
        3. Checks that the kfp imports are not included in the string when using kfp spec (kfp spec comes with kfp imports by default).

    Args:
        custom_code_contents: Code inside of the component, specified by the user.
        kfp_spec_bool: Boolean that specifies whether components are defined using kfp.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    component_base_task_file = component_base_task_file_jinja(custom_code_contents, kfp_spec_bool)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in component_base_task_file
        elif not is_included:
            assert snippet not in component_base_task_file


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE])]
)
def test_pipeline_runner_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests pipeline_runner_jinja, which generates code for the pipeline_runner.py 
       file to be written to the pipelines directory. There is one test case for this function:
        1. Checks for the apache license.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    pipeline_runner_py = pipeline_runner_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in pipeline_runner_py
        elif not is_included:
            assert snippet not in pipeline_runner_py


@pytest.mark.parametrize(
    '''components_list, custom_training_job_specs, pipeline_scaffold_contents, project_id,'''
    '''is_included, expected_output_snippets''',
    [
        (
            ['componentA','componentB','componentC'],
            [
                {
                    'component_spec': 'componentB',
                    'display_name': 'train-model-accelerated',
                    'machine_type': 'a2-highgpu-1g',
                    'accelerator_type': 'NVIDIA_TESLA_A100',
                    'accelerator_count': '1',
                }
            ],
           'Pipeline definition goes here', 'my-project', True,
            [GENERATED_LICENSE,
             'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component',
             'def upload_pipeline_spec',
             'componentA = load_custom_component',
             'componentB = load_custom_component',
             'componentC = load_custom_component',
             'componentB_custom_training_job_specs',
             'Pipeline definition goes here']
        ),
        (
            ['componentA','componentB','componentC'],
            None, 'Pipeline definition goes here', 'my-project',  True,
            [GENERATED_LICENSE,
             'def upload_pipeline_spec',
             'componentA = load_custom_component',
             'componentB = load_custom_component',
             'componentC = load_custom_component',
             'Pipeline definition goes here']
        ),
        (
            ['componentA','componentB','componentC'],
            None, 'Pipeline definition goes here', 'my-project',  False,
            ['from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component',
             'componentB_custom_training_job_specs']
        ),
    ]
)
def test_pipeline_jinja(
    components_list: list,
    custom_training_job_specs: list,
    pipeline_scaffold_contents: str,
    project_id: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests pipeline_jinja, which generates code for the pipeline.py 
       file to be written to the pipelines directory.
       There are three test cases for this function:
        1. Checks for the apache license and relevant code elements when custom_training_job_specs is not None.
        2. Checks for the apache license and relevant code elements when custom_training_job_specs is None.
        3. Checks that the output does not contain custom_training_job_specs code elements when custom_training_job_specs is None.

    Args:
        components_list: Contains the names or paths of all component yamls in the dir.
        custom_training_job_specs: Specifies the specs to run the training job with.
        pipeline_scaffold_contents: The contents of the pipeline scaffold file,
            which can be found at PIPELINE_CACHE_FILE.
        project_id: The project ID.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    pipeline_py = pipeline_jinja(
        components_list,
        custom_training_job_specs,
        pipeline_scaffold_contents,
        project_id)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in pipeline_py
        elif not is_included:
            assert snippet not in pipeline_py


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [PINNED_KFP_VERSION, 'google-cloud-aiplatform'])]
)
def test_pipeline_requirements_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests pipeline_requirements_jinja, which generates code for a requirements.txt
       to be written to the pipelines directory. There is one test case for this function:
        1. Checks for the pinned kfp version, and the google-cloud-aiplatform dep.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    pipeline_requirements_py = pipeline_requirements_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in pipeline_requirements_py
        elif not is_included:
            assert snippet not in pipeline_requirements_py


@pytest.mark.parametrize(
    'is_included, expected_output_snippets',
    [(True, [GENERATED_LICENSE, 'python:3.9-slim',
             'CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app'])]
)
def test_submission_service_dockerfile_jinja(
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests pipeline_requirements_jinja, which generates code for a Dockerfile to be
       written to the serivces/submission_service directory. There is one test case for this function:
        1. Checks for the apache license and relevant dockerfile elements.

    Args:
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    submission_service_dockerfile = submission_service_dockerfile_jinja()

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in submission_service_dockerfile
        elif not is_included:
            assert snippet not in submission_service_dockerfile


@pytest.mark.parametrize(
    'pipeline_job_submission_service_type, is_included, expected_output_snippets',
    [('cloud-functions', True, [PINNED_KFP_VERSION, 'google-cloud-aiplatform', 'functions-framework==3.*']),
     ('cloud-functions', False, ['gunicorn']),
     ('cloud-run', True, [PINNED_KFP_VERSION, 'google-cloud-aiplatform', 'gunicorn']),
     ('cloud-run', False, ['functions-framework==3.*']),]
)
def test_submission_service_requirements_jinja(
    pipeline_job_submission_service_type: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests submission_service_requirements_jinja, which generates code 
       for a requirements.txt to be written to the serivces/submission_service directory.
       There are four test cases for this function:
        1. Checks for the pinned kfp version, the google-cloud-aiplatform and function-framework deps when set to cloud-functions.
        2. Checks that gunicorn dep is not included when set to cloud-functions.
        3. Checks for the pinned kfp version, the google-cloud-aiplatform and gunicorn deps when set to cloud-run.
        4. Checks that functions-framework dep is not included when set to cloud-run.

    Args:
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    submission_service_requirements = submission_service_requirements_jinja(pipeline_job_submission_service_type=pipeline_job_submission_service_type)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in submission_service_requirements
        elif not is_included:
            assert snippet not in submission_service_requirements


@pytest.mark.parametrize(
    '''pipeline_root, pipeline_job_runner_service_account, pipeline_job_submission_service_type,'''
    '''project_id, is_included, expected_output_snippets''',
    [
        (
            'gs://my-bucket/pipeline-root', 'my-service-account@service.com', 'cloud-functions',
            'my-project', True,
            [GENERATED_LICENSE,
             'from google.cloud import aiplatform',
             'import functions_framework',
             '@functions_framework.http',
             'def process_request(request: flask.Request)',
             '''base64_message = request_json['data']['data']''']
        ),
        (
            'gs://my-bucket/pipeline-root', 'my-service-account@service.com', 'cloud-functions',
            'my-project', False,
            ['app = flask.Flask',
             '''@app.route('/', methods=['POST'])''',
             'request = flask.request',
             '''base64_message = request_json['message']['data']''',
             '''if __name__ == '__main__':''',
             '''app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))''']
        ),
        (
            'gs://my-bucket/pipeline-root', 'my-service-account@service.com', 'cloud-run',
            'my-project', True,
            [GENERATED_LICENSE,
             'from google.cloud import aiplatform',
             'app = flask.Flask',
             '''@app.route('/', methods=['POST'])''',
             'request = flask.request',
             '''base64_message = request_json['message']['data']''',
             '''if __name__ == '__main__':''',
             '''app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))''']
        ),
        (
            'gs://my-bucket/pipeline-root', 'my-service-account@service.com', 'cloud-run',
            'my-project', False,
            ['import functions_framework',
             '@functions_framework.http',
             'def process_request(request: flask.Request)',
             '''base64_message = request_json['data']['data']''']
        ),
    ]
)
def test_submission_service_main_jinja(
    pipeline_root: str,
    pipeline_job_runner_service_account: str,
    pipeline_job_submission_service_type: str,
    project_id: str,
    is_included: bool,
    expected_output_snippets: List[str]):
    """Tests submission_service_main_jinja, which generates content
       for main.py to be written to the serivces/submission_service directory. 
       There are four test cases for this function:
        1. Checks for functions_framework code elements when set to cloud-functions.
        2. Checks that Flask app code elements are not included when set to cloud-functions.
        3. Checks for Flask app code elements when set to cloud-run.
        4. Checks that functions_framework code elements are not included when set to cloud-run.

    Args:
        pipeline_root: GS location where to store metadata from pipeline runs.
        pipeline_job_runner_service_account: Service Account to runner PipelineJobs.
        pipeline_job_submission_service_type: The tool to host for the cloud submission service (e.g. cloud run, cloud functions).
        project_id: The project ID.
        is_included: Boolean that determines whether to check if the expected_output_snippets exist in the string or not.
        expected_output_snippets: Strings that are expected to be included (or not) based on the is_included boolean.
    """
    submission_service_main_py = submission_service_main_jinja(
        pipeline_root=pipeline_root,
        pipeline_job_runner_service_account=pipeline_job_runner_service_account,
        pipeline_job_submission_service_type=pipeline_job_submission_service_type,
        project_id=project_id)

    for snippet in expected_output_snippets:
        if is_included:
            assert snippet in submission_service_main_py
        elif not is_included:
            assert snippet not in submission_service_main_py
