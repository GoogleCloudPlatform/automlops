import os

from google.cloud import storage

from fastapi import FastAPI, Request
from transformers import AutoTokenizer, T5ForConditionalGeneration

BUCKET_NAME = 'automlops-sandbox-bucket' # Update
PREFIX = 'flan_t5_model/' # Update
OUTPUT_FOLDER = '../model-output-flan-t5-base'

app = FastAPI()

def download_model_artifacts():
    '''Download model artifacts from GCS to local container
       (HuggingFace does not support loading directly from GCS)
    '''
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)
    for blob in bucket.list_blobs(prefix=PREFIX):
        if '.' in blob.name.split('/')[-1]:
            blob.download_to_filename(OUTPUT_FOLDER + '/' + blob.name.split('/')[-1])

download_model_artifacts()

@app.get(os.environ['AIP_HEALTH_ROUTE'], status_code=200)
def health():
    return {"status": "healthy"}

@app.post(os.environ['AIP_PREDICT_ROUTE'])
async def predict(request: Request):
    body = await request.json()

    instances = body["instances"]

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(OUTPUT_FOLDER)

    # Load model
    model = T5ForConditionalGeneration.from_pretrained(OUTPUT_FOLDER)

    outputs = []
    for instance in instances:

        generated = model.generate(**tokenizer(instance, return_tensors="pt", padding=True), max_new_tokens=50)
        outputs.append([tokenizer.decode(t, skip_special_tokens=True) for t in generated])

    return {"predictions": [outputs]}
