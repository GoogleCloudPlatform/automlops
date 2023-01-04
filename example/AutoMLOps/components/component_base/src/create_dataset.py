import argparse
import json
from kfp.v2.components import executor

import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import *
from typing import *

def create_dataset(
    bq_table: str,
    output_data_path: OutputPath("Dataset"),
    project: str
):
    from google.cloud import bigquery
    import pandas as pd
    bq_client = bigquery.Client(project=project)


    def get_query(bq_input_table: str) -> str:
        """Generates BQ Query to read data.

        Args:
        bq_input_table: The full name of the bq input table to be read into
        the dataframe (e.g. <project>.<dataset>.<table>)
        Returns: A BQ query string.
        """
        return f"""
        SELECT *
        FROM `{bq_input_table}`
        """

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
    dataframe.to_csv(output_data_path)


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
