import argparse
import json
from kfp.v2.components import executor
import json
import pandas as pd
from google.cloud import storage
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import pickle
import os

def train_model(
    model_directory: str,
    data_path: str,
):
    """Trains a decision tree on the training data.

    Args:
        model_directory: GS location of saved model.,
        data_path: GS location where the training data.,
    """    
    
    def save_model(model, model_directory):
        """Saves a model to uri."""
        filename = f'model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(model, f)
        
        bucket_name = model_directory.split('/')[2]
        prefix='/'.join(model_directory.split('/')[3:])
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(os.path.join(prefix, filename))
        blob.upload_from_filename(filename)
    
    df = pd.read_csv(data_path)
    labels = df.pop("Class").tolist()
    data = df.values.tolist()
    x_train, x_test, y_train, y_test = train_test_split(data, labels)
    skmodel = DecisionTreeClassifier()
    skmodel.fit(x_train,y_train)
    score = skmodel.score(x_test,y_test)
    print('accuracy is:',score)
    
    output_uri = os.path.join(model_directory, f'model.pkl')
    save_model(skmodel, model_directory)

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
