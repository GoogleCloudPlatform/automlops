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
import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import *
from typing import *

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

    output_uri = os.path.join(model_directory, f'model.pkl')
    save_model(skmodel, output_uri)

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
