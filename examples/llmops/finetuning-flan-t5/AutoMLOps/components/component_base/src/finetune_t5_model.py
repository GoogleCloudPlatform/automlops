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

def finetune_t5_model(
    model_dir: str,
    epochs: int,
    eval_batch: int,
    logging_steps: int,
    lr: float,
    train_batch: int
):
    """Custom component that finetunes a Flan T5 base model.

    Args:
        model_dir: GCS directory to save the model and training artifacts.
        epochs: Total number of training epochs to perform.
        eval_batch: The batch size per GPU/TPU core/CPU for evaluation.
        logging_steps: Number of update steps between two logs.
        lr: The initial learning rate for AdamW optimizer.
        train_batch: The batch size per GPU/TPU core/CPU for training.
    """
    import glob
    import logging
    import os

    from google.cloud import storage

    from datasets import concatenate_datasets, load_dataset
    from huggingface_hub import HfFolder
    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments
    )
    from transformers.integrations import TensorBoardCallback
    import evaluate
    import nltk
    import numpy as np
    from nltk.tokenize import sent_tokenize

    MODEL_ID='google/flan-t5-base'
    DATASET_ID = 'samsum'

    def preprocess_function(sample, padding='max_length'):
        # add prefix to the input for t5
        inputs = ['summarize: ' + item for item in sample['dialogue']]

        # tokenize inputs
        model_inputs = tokenizer(inputs, max_length=max_source_length, padding=padding, truncation=True)

        # Tokenize targets with the `text_target` keyword argument
        labels = tokenizer(text_target=sample['summary'], max_length=max_target_length, padding=padding, truncation=True)

        # If we are padding here, replace all tokenizer.pad_token_id in the labels by -100 when we want to ignore
        # padding in the loss.
        if padding == 'max_length':
            labels['input_ids'] = [
                [(l if l != tokenizer.pad_token_id else -100) for l in label] for label in labels['input_ids']
            ]

        model_inputs['labels'] = labels['input_ids']
        return model_inputs

    # helper function to postprocess text
    def postprocess_text(preds, labels):
        preds = [pred.strip() for pred in preds]
        labels = [label.strip() for label in labels]

        # rougeLSum expects newline after each sentence
        preds = ['\n'.join(sent_tokenize(pred)) for pred in preds]
        labels = ['\n'.join(sent_tokenize(label)) for label in labels]

        return preds, labels

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        # Replace -100 in the labels as we can't decode them.
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        # Some simple post-processing
        decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

        result = metric.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)
        result = {k: round(v * 100, 4) for k, v in result.items()}
        prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
        result['gen_len'] = np.mean(prediction_lens)
        return result

    def upload_to_gcs(local_directory_path: str, gs_directory_path: str):
        client = storage.Client()

        # extract GCS bucket_name
        bucket_name = gs_directory_path.split('/')[2] # without gs://
        # extract GCS object_name
        object_name = '/'.join(gs_directory_path.split('/')[3:])

        rel_paths = glob.glob(local_directory_path + '/**', recursive=True)
        bucket = client.get_bucket(bucket_name)
        for local_file in rel_paths:
            remote_path = f'''{object_name}{'/'.join(local_file.split(os.sep)[1:])}'''
            logging.info(remote_path)
            if os.path.isfile(local_file):
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_file)

    # Load dataset
    dataset = load_dataset(DATASET_ID)
    # Load tokenizer of FLAN-t5-base
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    # load model from the hub
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)

    nltk.download('punkt')
    # Metric
    metric = evaluate.load('rouge')

    # Hugging Face repository id
    repository_id = f'''{MODEL_ID.split('/')[1]}-{DATASET_ID}'''

    # The maximum total input sequence length after tokenization.
    # Sequences longer than this will be truncated, sequences shorter will be padded.
    tokenized_inputs = concatenate_datasets([dataset['train'],
                                             dataset['test']]).map(lambda x: tokenizer(x['dialogue'],truncation=True),
                                                                   batched=True, remove_columns=['dialogue', 'summary'])
    max_source_length = max([len(x) for x in tokenized_inputs['input_ids']])
    print(f'Max source length: {max_source_length}')

    # The maximum total sequence length for target text after tokenization.
    # Sequences longer than this will be truncated, sequences shorter will be padded."
    tokenized_targets = concatenate_datasets([dataset['train'],
                                              dataset['test']]).map(lambda x: tokenizer(x['summary'], truncation=True),
                                                                    batched=True, remove_columns=['dialogue', 'summary'])
    max_target_length = max([len(x) for x in tokenized_targets['input_ids']])
    print(f'Max target length: {max_target_length}')

    tokenized_dataset = dataset.map(preprocess_function, batched=True, remove_columns=['dialogue', 'summary', 'id'])
    print(f'''Keys of tokenized dataset: {list(tokenized_dataset['train'].features)}''')

    # we want to ignore tokenizer pad token in the loss
    label_pad_token_id = -100
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=label_pad_token_id,
        pad_to_multiple_of=8
    )

    # Define training args
    training_args = Seq2SeqTrainingArguments(
        output_dir=repository_id,
        per_device_train_batch_size=train_batch,
        per_device_eval_batch_size=eval_batch,
        predict_with_generate=True,
        fp16=False, # Overflows with fp16
        learning_rate=lr,
        num_train_epochs=epochs,
        # logging & evaluation strategies
        logging_dir=os.environ['AIP_TENSORBOARD_LOG_DIR'],
        #logging_dir=f'{repository_id}/logs',
        logging_strategy='steps',
        logging_steps=logging_steps,
        evaluation_strategy='epoch',
        save_strategy='epoch',
        save_total_limit=2,
        load_best_model_at_end=True,
        # metric_for_best_model="overall_f1",
        # push to hub parameters
        report_to='tensorboard',
        push_to_hub=False,
        hub_strategy='every_save',
        hub_model_id=repository_id,
        hub_token=HfFolder.get_token(),
    )

    # Create Trainer instance
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset['train'],
        eval_dataset=tokenized_dataset['test'],
        compute_metrics=compute_metrics,
        callbacks=[TensorBoardCallback()]
    )

    # Start training
    logging.info('Training ....')
    trainer.train()
    trainer.evaluate()

    # Save tokenizer and model locally
    tokenizer.save_pretrained(f'model_tokenizer')
    trainer.save_model(f'model_output')

    logging.info('Saving model and tokenizer to GCS ....')

    # Upload model to GCS
    upload_to_gcs('model_output', model_dir)
    # Upload tokenizer to GCS
    upload_to_gcs('model_tokenizer', model_dir)

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
