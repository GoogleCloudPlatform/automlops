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

def custom_train_model(
    metrics: Output[Metrics],
    model_dir: str,
    output_model: Output[Model],
    lr: float = 0.001,
    epochs: int = 10,
    steps: int = 200,
    distribute: str = 'single'
):

    import faulthandler
    import os
    import sys

    import tensorflow as tf
    import tensorflow_datasets as tfds
    from tensorflow.python.client import device_lib

    faulthandler.enable()
    tfds.disable_progress_bar()

    print('Component start')

    print(f'Python Version = {sys.version}')
    print(f'TensorFlow Version = {tf.__version__}')
    print(f'TF_CONFIG = {os.environ.get("TF_CONFIG", "Not found")}')
    print(f'DEVICES = {device_lib.list_local_devices()}')

    # Single Machine, single compute device
    if distribute == 'single':
        if tf.test.is_gpu_available():
            strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
        else:
            strategy = tf.distribute.OneDeviceStrategy(device="/cpu:0")
    # Single Machine, multiple compute device
    elif distribute == 'mirror':
        strategy = tf.distribute.MirroredStrategy()
    # Multiple Machine, multiple compute device
    elif distribute == 'multi':
        strategy = tf.distribute.experimental.MultiWorkerMirroredStrategy()

    # Multi-worker configuration
    print(f'num_replicas_in_sync = {strategy.num_replicas_in_sync}')

    # Preparing dataset
    BUFFER_SIZE = 10000
    BATCH_SIZE = 64

    def preprocess_data(image, label):
        '''Resizes and scales images.'''

        image = tf.image.resize(image, (300,300))
        return tf.cast(image, tf.float32) / 255., label

    def create_dataset(batch_size: int):
        '''Loads Cassava dataset and preprocesses data.'''

        data, info = tfds.load(name='cassava', as_supervised=True, with_info=True)
        number_of_classes = info.features['label'].num_classes
        train_data = data['train'].map(preprocess_data,
                                       num_parallel_calls=tf.data.experimental.AUTOTUNE)
        train_data  = train_data.cache().shuffle(BUFFER_SIZE).repeat()
        train_data  = train_data.batch(batch_size)
        train_data  = train_data.prefetch(tf.data.experimental.AUTOTUNE)

        # Set AutoShardPolicy
        options = tf.data.Options()
        options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.DATA
        train_data = train_data.with_options(options)

        return train_data, number_of_classes

    # Build the ResNet50 Keras model    
    def create_model(number_of_classes: int, lr: int = 0.001):
        '''Creates and compiles pretrained ResNet50 model.'''

        base_model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False)
        x = base_model.output
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dense(1016, activation='relu')(x)
        predictions = tf.keras.layers.Dense(number_of_classes, activation='softmax')(x)
        model = tf.keras.Model(inputs=base_model.input, outputs=predictions)

        model.compile(
            loss=tf.keras.losses.sparse_categorical_crossentropy,
            optimizer=tf.keras.optimizers.Adam(lr),
            metrics=['accuracy'])
        return model

    # Train the model
    NUM_WORKERS = strategy.num_replicas_in_sync
    # Here the batch size scales up by number of workers since
    # `tf.data.Dataset.batch` expects the global batch size.
    GLOBAL_BATCH_SIZE = BATCH_SIZE * NUM_WORKERS
    train_dataset, number_of_classes = create_dataset(GLOBAL_BATCH_SIZE)

    with strategy.scope():
        # Creation of dataset, and model building/compiling need to be within `strategy.scope()`.
        resnet_model = create_model(number_of_classes, lr)

    h = resnet_model.fit(x=train_dataset, epochs=epochs, steps_per_epoch=steps)
    acc = h.history['accuracy'][-1]
    resnet_model.save(model_dir)

    output_model.path = model_dir
    metrics.log_metric('accuracy', (acc * 100.0))
    metrics.log_metric('framework', 'Tensorflow')


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
