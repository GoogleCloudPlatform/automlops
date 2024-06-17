    # Copyright 2023 Google LLC
    #
    # Licensed under the Apache License, Version 2.0 (the "License");
    # you may not use this file except in compliance with the License.
    # You may obtain a copy of the License at
    #
    #     https://www.apache.org/licenses/LICENSE-2.0
    #
    # Unless required by applicable law or agreed to in writing, software
    # distributed under the License is distributed on an "AS IS" BASIS,
    # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    # See the License for the specific language governing permissions and
    # limitations under the License.
"""Basic integration test using the dry beans dataset"""

import os
import time
import datetime
import helpers
from google_cloud_automlops import AutoMLOps
from google_cloud_automlops.utils.utils import (
    read_yaml_file
)
from google_cloud_automlops.utils.constants import (
    GENERATED_DEFAULTS_FILE,
)

@AutoMLOps.component(
    packages_to_install=[
        'google-cloud-bigquery',
        'pandas',
        'pyarrow',
        'db_dtypes',
        'fsspec',
        'gcsfs'
    ]
)
def create_dataset(bq_table: str, data_path: str, project_id: str):
    """Custom component that takes in a BQ table and writes it to GCS.

    Args:
        bq_table: The source biquery table.
        data_path: The gcs location to write the csv.
        project_id: The project ID.
    """
    # pylint: disable=unused-import
    import pandas as pd
    from google.cloud import bigquery
    from sklearn import preprocessing

    get_query = f'SELECT * FROM `{bq_table}`'
    bq_client = bigquery.Client(project=project_id)

    dataframe = bq_client.query(get_query).to_dataframe()
    le = preprocessing.LabelEncoder()
    dataframe['Class'] = le.fit_transform(dataframe['Class'])
    dataframe.to_csv(data_path, index=False)

@AutoMLOps.component(
    packages_to_install=[
        'scikit-learn==1.2.0',
        'pandas',
        'joblib',
        'tensorflow'
    ]
)
def train_model(data_path: str, model_directory: str):
    """Custom component that trains a decision tree on the training data.

    Args:
        data_path: GS location where the training data.
        model_directory: GS location of saved model.
    """
    import pickle
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    import pandas as pd
    import tensorflow as tf

    df = pd.read_csv(data_path)
    labels = df.pop('Class').tolist()
    data = df.values.tolist()
    x_train, x_test, y_train, y_test = train_test_split(data, labels)
    skmodel = DecisionTreeClassifier()
    skmodel.fit(x_train,y_train)
    score = skmodel.score(x_test,y_test)
    print('accuracy is:',score)

    output_uri = os.path.join(model_directory, 'model.pkl')

    # Write the file as a pickled object to disk
    with tf.io.gfile.GFile(output_uri, 'w') as f:
        pickle.dump(skmodel, f)


# ## Uploading & Deploying the Model
# Define a custom component for uploading and deploying a model in Vertex AI,
# using `@AutoMLOps.component`. Import statements and helper functions must
# be added inside the function.

@AutoMLOps.component(
    packages_to_install=[
        'google-cloud-aiplatform'
    ]
)
def deploy_model(model_directory: str, project_id: str, region: str):
    """Custom component that trains a decision tree on the training data.

    Args:
        model_directory: GS location of saved model.
        project_id: Project_id.
        region: Region.
    """

    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=region)
    # Check if model exists
    models = aiplatform.Model.list()
    model_name = 'beans-model'
    if 'beans-model' in (m.name for m in models):
        parent_model = model_name
        model_id = None
        is_default_version=False
        version_aliases=['experimental', 'challenger', 'custom-training', \
                         'decision-tree']
        version_description='challenger version'
    else:
        parent_model = None
        model_id = model_name
        is_default_version=True
        version_aliases=['champion', 'custom-training', 'decision-tree']
        version_description='first version'

    serving_container = \
        'us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest'
    uploaded_model = aiplatform.Model.upload(
        artifact_uri = model_directory,
        model_id=model_id,
        display_name=model_name,
        parent_model=parent_model,
        is_default_version=is_default_version,
        version_aliases=version_aliases,
        version_description=version_description,
        serving_container_image_uri=serving_container,
        serving_container_ports=[8080],
        labels={'created_by': 'automlops-team'},
    )

    uploaded_model.deploy(
        machine_type='n1-standard-4',
        deployed_model_display_name='deployed-beans-model')

# ## Define the Pipeline
# Define your pipeline using `@AutoMLOps.pipeline`. You can optionally give
# the pipeline a name and description. Define the structure by listing the
# components to be called in your pipeline; use `.after` to specify the
# order of execution.

@AutoMLOps.pipeline
def pipeline(bq_table: str,
            model_directory: str,
            data_path: str,
            project_id: str,
            region: str,
            ):

    create_dataset_task = create_dataset(
        bq_table=bq_table,
        data_path=data_path,
        project_id=project_id)

    train_model_task = train_model(
        model_directory=model_directory,
        data_path=data_path).after(create_dataset_task)

    deploy_model(
        model_directory=model_directory,
        project_id=project_id,
        region=region).after(train_model_task)


def test_beans_training_model():
    # Importing here to avoid conflict with repeated import in deploy_model
    from google.cloud import aiplatform

    project_id = ''
    model_id = ''
    ## Define the Pipeline Arguments
    timestamp = datetime.datetime.now()
    model_directory = f'gs://{project_id}-bucket/trained_models/{timestamp}'
    pipeline_params = {
        'bq_table': f'{project_id}.test_dataset.dry-beans',
        'model_directory': model_directory,
        'data_path': f'gs://{project_id}-{model_id}-bucket/data.csv',
        'project_id': project_id,
        'region': 'us-central1'
    }

    AutoMLOps.generate(project_id=project_id,
                    pipeline_params=pipeline_params,
                    use_ci=True,
                    naming_prefix=model_id
    )


    AutoMLOps.provision(hide_warnings=False)
    time.sleep(300)
    print('HIT PROVISION')

    # Assert that GCP infrastructure was stood up with the correct names.
    defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
    helpers.assert_successful_provisioning(defaults)

    # Assert that Vertex AI endpoint was created and returns predictions.
    aiplatform.init(project=project_id)
    endpoints = aiplatform.Endpoint.list()
    endpoint_name = endpoints[0].resource_name
    endpoint = aiplatform.Endpoint(endpoint_name)
    data = [[
        28395.0,
        610.291,
        208.1781167,
        173.888747,
        1.197191424,
        0.5498121871,
        28715,
        190.1410973,
        0.7639225182,
        0.9888559986,
        0.9580271263,
        0.9133577548,
        0.007331506135,
        0.003147289167,
        0.8342223882,
        0.998723889
        ]]

    # Send the prediction request
    prediction = endpoint.predict(instances=data)
    prediction_value = int(prediction.predictions[0])
    assert prediction_value in range(7)
