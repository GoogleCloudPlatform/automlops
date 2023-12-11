import datetime
import airflow
from airflow.operators import bash_operator
from airflow.operators.python import PythonOperator
from airflow.operators.python_operator import PythonVirtualenvOperator

# If you are running Airflow in more than one time zone
# see https://airflow.apache.org/docs/apache-airflow/stable/timezone.html
# for best practices
YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)
PROJECT_ID = 'airflow-sandbox-392816'
MODEL_ID = 'dry-beans-dt'

default_args = {
    "owner": "Composer Example",
    "depends_on_past": False,
    "email": [""],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
    "start_date": YESTERDAY,
}

def hello_world(name: str, pipeline_params, PROJECT_ID, MODEL_ID):
    import pandas as pd
    import datetime
    print(pipeline_params['model_directory'])
    df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
    print(df.to_string())
    print(f"hello world {name}")


def create_dataset(
    bq_table: str,
    data_path: str,
    project_id: str,
    pipeline_params
):
    """Custom component that takes in a BQ table and writes it to GCS.

    Args:
        bq_table: The source biquery table.
        data_path: The gcs location to write the csv.
        project_id: The project ID.
    """
    from google.cloud import bigquery
    import pandas as pd
    import sklearn
    from sklearn import preprocessing
    
    bq_client = bigquery.Client(project=project_id)
    print(f"THIS IS THE TIME STAMP: {pipeline_params['model_directory']}")


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

def train_model(
    data_path: str,
    model_directory: str
):
    """Custom component that trains a decision tree on the training data.

    Args:
        data_path: GS location of the training data.
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

def deploy_model(
    model_directory: str,
    project_id: str,
    region: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction.

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

    serving_container = 'us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-2:latest'
    uploaded_model = aiplatform.Model.upload(
        artifact_uri=model_directory,
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
    

with airflow.DAG(
    "composer_sample_pyenv_dag",
    catchup=False,
    default_args=default_args,
) as dag:

    timestamp = datetime.datetime.now()
    pipeline_params = {
        'bq_table': f'{PROJECT_ID}.test_dataset.dry-beans',
        'model_directory': f'gs://{PROJECT_ID}-{MODEL_ID}-bucket/trained_models/airflow_model_test_run',
        'data_path': f'gs://{PROJECT_ID}-{MODEL_ID}-bucket/data.csv',
        'project_id': PROJECT_ID,
        'region': 'us-central1'
    }

    hello_world_task = PythonVirtualenvOperator(
        task_id='hello_world_task',
        python_callable=hello_world,
        requirements=['pandas', 'numpy'],
        op_kwargs={
            'name': 'John',
            'pipeline_params': pipeline_params,
            'PROJECT_ID': PROJECT_ID,
            'MODEL_ID': MODEL_ID},
    )

    create_dataset_task = PythonVirtualenvOperator(
        task_id='create_dataset_task',
        python_callable=create_dataset,
        requirements=["google-cloud-bigquery", "pandas", "scikit-learn"],
        op_kwargs={
            "bq_table": pipeline_params["bq_table"],
            "data_path": pipeline_params["data_path"],
            "project_id": pipeline_params["project_id"],
            'pipeline_params': pipeline_params
        },
    )

    train_model_task = PythonVirtualenvOperator(
        task_id="train_model_task",
        python_callable=train_model,
        requirements=[
            "scikit-learn==1.2.0",
            "pandas",
            "joblib",
            "tensorflow",
        ],
        op_kwargs={
            "data_path": pipeline_params["data_path"],
            "model_directory": pipeline_params["model_directory"],
        },
    )

    deploy_model_task = PythonVirtualenvOperator(
        task_id="deploy_model_task",
        python_callable=deploy_model,
        requirements=["google-cloud-aiplatform"],
        op_kwargs={
            "model_directory": pipeline_params["model_directory"],
            "project_id": pipeline_params["project_id"],
            "region": pipeline_params["region"],
        },
    )

    hello_world_task >> create_dataset_task >> train_model_task >> deploy_model_task


