# gcloud builds submit serving --tag us-central1-docker.pkg.dev/automlops-sandbox/vertex-mlops-af/finetuning_flan_t5_base:latest
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY ./app /app
COPY requirements.txt /app/requirements.txt
COPY ./model-output-flan-t5-base/ /model-output-flan-t5-base/

# install dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8080

# Start the app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app", "--workers", "1", "--timeout", "180", "-k", "uvicorn.workers.UvicornWorker"]