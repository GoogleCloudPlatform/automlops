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
#
# DISCLAIMER: This code is generated as part of the AutoMLOps output.

import argparse
import json
from kfp.v2.components import executor
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

def main():
    """Main executor."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--executor_input', type=str)
    parser.add_argument('--function_to_execute', type=str)

    args, _ = parser.parse_known_args()
    executor_input = json.loads(args.executor_input)
    function_to_execute = globals()[args.function_to_execute]

    executor.Executor(
        executor_input=executor_input,
        function_to_execute=function_to_execute).execute()

if __name__ == '__main__':
    main()
