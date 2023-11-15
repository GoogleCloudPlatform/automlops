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

import pytest
import subprocess
import os
import logging
import time
from google.cloud import aiplatform
from .. import helpers



def test_beans_training_model():

    # Install AutoMLOps from [PyPI](https://pypi.org/project/google-cloud-automlops/), or locally by cloning the repo and running `pip install .`
    helpers.execute_process('pip3 install google-cloud-automlops', False)

    # Set your project ID below.
    PROJECT_ID = 'airflow-sandbox-392816'  # @param {type:"string"}
    helpers.execute_process(f"gcloud config set project {PROJECT_ID}", False)

    # Set your Model ID below.
    MODEL_ID = 'dry-beans-dt'

    # Import AutoMLOps
    from google_cloud_automlops import AutoMLOps

    # ## Data Loading
    # Define a custom component for loading and creating a dataset using `@AutoMLOps.component`. Import statements and helper functions must be added inside the function. Provide parameter type hints.
    # 
    # **Note: we currently only support python primitive types for component parameters. If you would like to use something more advanced, please use the Kubeflow spec instead (see below in this notebook).**

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
    def create_dataset(
        bq_table: str,
        data_path: str,
        project_id: str
    ):
        """Custom component that takes in a BQ table and writes it to GCS.

        Args:
            bq_table: The source biquery table.
            data_path: The gcs location to write the csv.
            project_id: The project ID.
        """
        from google.cloud import bigquery
        import pandas as pd
        from sklearn import preprocessing

        bq_client = bigquery.Client(project=project_id)

        def get_query(bq_input_table: str) -> str:
            """Generates BQ Query to read data.

            Args:
            bq_input_table: The full name of the bq input table to be read into
            the dataframe (e.g. <project>.<dataset>.<table>)
            Returns: A BQ query string.
            """
            return f'''
            SELECT *
            FROM `{bq_input_table}`
            '''

        def load_bq_data(query: str, client: bigquery.Client) -> pd.DataFrame:
            """Loads data from bq into a Pandas Dataframe for EDA.
            Args:
            query: BQ Query to generate data.
            client: BQ Client used to execute query.
            Returns:
            pd.DataFrame: A dataframe with the requested data.
            """
            df = client.query(query).to_dataframe()
            return df

        dataframe = load_bq_data(get_query(bq_table), bq_client)
        le = preprocessing.LabelEncoder()
        dataframe['Class'] = le.fit_transform(dataframe['Class'])
        dataframe.to_csv(data_path, index=False)

    # ## Model Training
    # Define a custom component for training a model using `@AutoMLOps.component`. Import statements and helper functions must be added inside the function.

    @AutoMLOps.component(
        packages_to_install=[
            'scikit-learn==1.2.0',
            'pandas',
            'joblib',
            'tensorflow'
        ]
    )
    def train_model(
        data_path: str,
        model_directory: str
    ):
        """Custom component that trains a decision tree on the training data.

        Args:
            data_path: GS location where the training data.
            model_directory: GS location of saved model.
        """
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import train_test_split
        import pandas as pd
        import tensorflow as tf
        import pickle
        import os

        def save_model(model, uri):
            """Saves a model to uri."""
            with tf.io.gfile.GFile(uri, 'w') as f:
                pickle.dump(model, f)

        df = pd.read_csv(data_path)
        labels = df.pop('Class').tolist()
        data = df.values.tolist()
        x_train, x_test, y_train, y_test = train_test_split(data, labels)
        skmodel = DecisionTreeClassifier()
        skmodel.fit(x_train,y_train)
        score = skmodel.score(x_test,y_test)
        print('accuracy is:',score)

        output_uri = os.path.join(model_directory, 'model.pkl')
        save_model(skmodel, output_uri)

    # ## Uploading & Deploying the Model
    # Define a custom component for uploading and deploying a model in Vertex AI, using `@AutoMLOps.component`. Import statements and helper functions must be added inside the function.

    @AutoMLOps.component(
        packages_to_install=[
            'google-cloud-aiplatform'
        ]
    )
    def deploy_model(
        model_directory: str,
        project_id: str,
        region: str
    ):
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
            version_aliases=['experimental', 'challenger', 'custom-training', 'decision-tree']
            version_description='challenger version'
        else:
            parent_model = None
            model_id = model_name
            is_default_version=True
            version_aliases=['champion', 'custom-training', 'decision-tree']
            version_description='first version'

        serving_container = 'us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest'
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

        endpoint = uploaded_model.deploy(
            machine_type='n1-standard-4',
            deployed_model_display_name='deployed-beans-model')

    # ## Define the Pipeline
    # Define your pipeline using `@AutoMLOps.pipeline`. You can optionally give the pipeline a name and description. Define the structure by listing the components to be called in your pipeline; use `.after` to specify the order of execution.

    @AutoMLOps.pipeline #(name='automlops-pipeline', description='This is an optional description')
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

        deploy_model_task = deploy_model(
            model_directory=model_directory,
            project_id=project_id,
            region=region).after(train_model_task)


    ## Define the Pipeline Arguments
    import datetime
    pipeline_params = {
        'bq_table': f'{PROJECT_ID}.test_dataset.dry-beans',
        'model_directory': f'gs://{PROJECT_ID}-bucket/trained_models/{datetime.datetime.now()}',
        'data_path': f'gs://{PROJECT_ID}-{MODEL_ID}-bucket/data.csv',
        'project_id': PROJECT_ID,
        'region': 'us-central1'
    }

    AutoMLOps.generate(project_id=PROJECT_ID,
                    pipeline_params=pipeline_params,
                    use_ci=True,
                    naming_prefix=MODEL_ID
    )

    # Assert that files and directories were created with the correct names.
    expected_AMO_cache_files = ['create_dataset.yaml', 'deploy_model.yaml', 'pipeline_scaffold.py', 'train_model.yaml']
    expected_AMO_directory = ['.gitignore', 'README.md', 'cloudbuild.yaml', 'components', 'configs', 'images', 'pipelines', 'provision', 'scripts', 'services']

    assert sorted(os.listdir('./.AutoMLOps-cache')) == expected_AMO_cache_files
    assert sorted(os.listdir('./AutoMLOps')) == expected_AMO_directory

    AutoMLOps.provision(hide_warnings=False)
    time.sleep(300)
      
    # Assert that GCP infrastructure was stood up with the correct names.
    helpers.assert_repository_exists(repository_name="dry-beans-dt-repository")
    helpers.assert_build_trigger_exists(trigger_name="dry-beans-dt-build-trigger")
    helpers.assert_scheduler_job_exists(scheduler_name="dry-beans-dt-schedule")

    AutoMLOps.deploy(precheck=True, hide_warnings=False)
    time.sleep(600)

    # Assert that Vertex AI endpoint was created and returns predictions.
    aiplatform.init(project=PROJECT_ID)
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
