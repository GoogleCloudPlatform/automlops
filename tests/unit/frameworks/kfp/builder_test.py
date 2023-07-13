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

"""Unit tests for kfp builder module."""

# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring

import json
import os
from typing import List

import pytest
import pytest_mock

from AutoMLOps.frameworks.kfp.builder import (
    build_component,
    build_pipeline
)
import AutoMLOps.utils.utils
from AutoMLOps.utils.utils import (
    make_dirs,
    read_yaml_file,
    write_yaml_file
)

DEFAULTS = {
    'gcp': {
        'af_registry_location': 'us-central1',
        'project_id': 'my_project',
        'af_registry_name': 'my_af_registry',
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
            'image': 'us-central1-docker.pkg.dev/my_project/my_af_registry/components/component_base:latest',
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
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder,
                        'BASE_DIR', 
                        f'{tmpdir}' + '/')
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder,
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
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder,
                        'BASE_DIR',
                        f'{tmpdir}' + '/')
    mocker.patch.object(AutoMLOps.frameworks.kfp.builder,
                        'GENERATED_DEFAULTS_FILE',
                        defaults_dict['path'])
    mocker.patch.object(AutoMLOps.utils.utils,
                        'CACHE_DIR',
                        '.')

    # Create required directory and file for build_pipeline
    make_dirs([f'{tmpdir}/pipelines/runtime_parameters'])
    os.system(f'touch {tmpdir}/pipelines/pipeline.py')
    build_pipeline(custom_training_job_specs, pipeline_parameter_values)

    # Ensure correct files were created
    assert os.path.exists(f'{tmpdir}/pipelines/pipeline.py')
    assert os.path.exists(f'{tmpdir}/pipelines/pipeline_runner.py')
    assert os.path.exists(f'{tmpdir}/pipelines/runtime_parameters/pipeline_parameter_values.json')

    # Ensure pipeline_parameter_values.json was created as expected
    with open(f'{tmpdir}/pipelines/runtime_parameters/pipeline_parameter_values.json', mode='r', encoding='utf-8') as f:
        pipeline_params_dict = json.load(f)
    assert pipeline_params_dict == pipeline_parameter_values

    # Fetch pipeline.py and assert that it contains expected keywords
    keywords = [
        'Apache License',
        'import kfp',
        'parser = argparse.ArgumentParser()',
        'args = parser.parse_args',
        'pipeline = create_training_pipeline']
    keywords += json.dumps(custom_training_job_specs, indent=4)
    with open(f'{tmpdir}/pipelines/pipeline.py', mode='r', encoding='utf-8') as file:
        pipeline_content = file.read()
    for keyword in keywords:
        assert keyword in pipeline_content
