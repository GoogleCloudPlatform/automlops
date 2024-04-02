# Copyright 2024 Google LLC. All Rights Reserved.
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
import argparse
import subprocess

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

def load_data(filename: str, project_id: str):
    # Construct a BigQuery client object.
    client = bigquery.Client(project=project_id)

    dataset_id = f'{project_id}.test_dataset'
    table_id = 'test_dataset.dry_beans_inferencing'

    # Construct a full Dataset object to send to the API.
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = 'US'

    try:
        client.get_dataset(dataset_id)
        print(f'Dataset {dataset_id} already exists')
    except NotFound:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f'Created dataset {client.project}.{dataset.dataset_id}')
    try:
        client.get_table(table_id)
        print(f'Table {table_id} already exists')
    except NotFound:
        write_table(table_id, filename)

def write_table(table_id: str, filename: str):
    try:
        cmd = f'bq load --skip_leading_rows=1 --autodetect {table_id} {filename}'
        subprocess.check_output([cmd], shell=True, stderr=subprocess.STDOUT)
        print(f'Uploaded data to table {table_id}')
    except Exception as err:
        raise Exception(f'Error uploading data. {err}') from err

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str,
                        help='The project id.')
    parser.add_argument('--file', type=str,
                        help='The csv file to upload.')
    args = parser.parse_args()
    load_data(args.file, args.project)
