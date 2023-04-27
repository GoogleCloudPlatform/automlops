from AutoMLOps import BuilderUtils

LEFT_BRACKET = '{'
RIGHT_BRACKET = '}'
NEWLINE = '\n'

class AutoMLOps():
    
    def __init__(self, defaults_file, top_folder, run_local):
        
        defaults = BuilderUtils.read_yaml_file(defaults_file)
        self.top_folder = top_folder
        self.run_local = run_local
        
        self.af_registry_name = defaults['gcp']['af_registry_name']
        self.af_registry_location = defaults['gcp']['af_registry_location']
        self.project_id = defaults['gcp']['project_id']
        self.gs_bucket_name = defaults['gcp']['gs_bucket_name']
        self.bucket_location = defaults['gcp']['gs_bucket_location']
        self.pipeline_region = defaults['pipelines']['pipeline_region']
        self.pipeline_runner_service_account = defaults['gcp']['pipeline_runner_service_account']
        self.cloud_source_repository = defaults['gcp']['cloud_source_repository']
        self.cloud_source_repository_branch = defaults['gcp']['cloud_source_repository_branch']
        self.cb_trigger_location = defaults['gcp']['cb_trigger_location']
        self.cb_trigger_name = defaults['gcp']['cb_trigger_name']
        self.cloud_tasks_queue_location = defaults['gcp']['cloud_tasks_queue_location']
        self.cloud_tasks_queue_name = defaults['gcp']['cloud_tasks_queue_name']
        self.vpc_connector = defaults['gcp']['vpc_connector']
        self.cloud_run_name = defaults['gcp']['cloud_run_name']
        self.cloud_run_location = defaults['gcp']['cloud_run_location']
        self.cloud_schedule_pattern = defaults['gcp']['cloud_schedule_pattern']
        
    def _build_pipeline_spec(self):
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Builds the pipeline specs\n'
            f'# This script should run from the {self.top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline --config $CONFIG_FILE\n')
        
    def _build_components(self):
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Submits a Cloud Build job that builds and deploys the components\n'
            f'# This script should run from the {self.top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n')
        
    def _run_pipeline(self):
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Submits the PipelineJob to Vertex AI\n'
            f'# This script should run from the {self.top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE\n')
    
    def _run_all(self):
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Builds components, pipeline specs, and submits the PipelineJob.\n'
            f'# This script should run from the {self.top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            '''GREEN='\033[0;32m'\n'''
            '''NC='\033[0m'\n'''
            '\n'
            'echo -e "${GREEN} BUILDING COMPONENTS ${NC}"\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n'
            '\n'
            'echo -e "${GREEN} BUILDING PIPELINE SPEC ${NC}"\n'
            './scripts/build_pipeline_spec.sh\n'
            '\n'
            'echo -e "${GREEN} RUNNING PIPELINE JOB ${NC}"\n'
            './scripts/run_pipeline.sh\n')
        
    def _create_resources_script(self):
        create_resources_script = (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
            f'\n'
            f'''GREEN='\033[0;32m'\n'''
            f'''NC='\033[0m'\n'''
            f'''AF_REGISTRY_NAME={self.af_registry_name}\n'''
            f'''AF_REGISTRY_LOCATION={self.af_registry_location}\n'''
            f'''PROJECT_ID={self.project_id}\n'''
            f'''PROJECT_NUMBER=`gcloud projects describe {self.project_id} --format 'value(projectNumber)'`\n'''
            f'''BUCKET_NAME={self.gs_bucket_name}\n'''
            f'''BUCKET_LOCATION={self.pipeline_region}\n'''
            f'''SERVICE_ACCOUNT_NAME={self.pipeline_runner_service_account.split('@')[0]}\n'''
            f'''SERVICE_ACCOUNT_FULL={self.pipeline_runner_service_account}\n'''
            f'''CLOUD_SOURCE_REPO={self.cloud_source_repository}\n'''
            f'''CLOUD_SOURCE_REPO_BRANCH={self.cloud_source_repository_branch}\n'''
            f'''CB_TRIGGER_LOCATION={self.cb_trigger_location}\n'''
            f'''CB_TRIGGER_NAME={self.cb_trigger_name}\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION={self.cloud_tasks_queue_location}\n'''
            f'''CLOUD_TASKS_QUEUE_NAME={self.cloud_tasks_queue_name}\n'''
            f'\n'
            f'echo -e "$GREEN Updating required API services in project $PROJECT_ID $NC"\n'
            f'gcloud services enable cloudresourcemanager.googleapis.com \{NEWLINE}'
            f'  aiplatform.googleapis.com \{NEWLINE}'
            f'  artifactregistry.googleapis.com \{NEWLINE}'
            f'  cloudbuild.googleapis.com \{NEWLINE}'
            f'  cloudscheduler.googleapis.com \{NEWLINE}'
            f'  cloudtasks.googleapis.com \{NEWLINE}'
            f'  compute.googleapis.com \{NEWLINE}'
            f'  iam.googleapis.com \{NEWLINE}'
            f'  iamcredentials.googleapis.com \{NEWLINE}'
            f'  ml.googleapis.com \{NEWLINE}'
            f'  run.googleapis.com \{NEWLINE}'
            f'  storage.googleapis.com \{NEWLINE}'
            f'  sourcerepo.googleapis.com\n'
            f'\n'
            f'echo -e "$GREEN Checking for Artifact Registry: $AF_REGISTRY_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep -E "(^|[[:blank:]])$AF_REGISTRY_NAME($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Artifact Registry: ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \{NEWLINE}'
            f'    --repository-format=docker \{NEWLINE}'
            f'    --location=$AF_REGISTRY_LOCATION \{NEWLINE}'
            f'    --project="$PROJECT_ID" \{NEWLINE}'
            f'    --description="Artifact Registry ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} in ${LEFT_BRACKET}AF_REGISTRY_LOCATION{RIGHT_BRACKET}." \n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Artifact Registry: ${LEFT_BRACKET}AF_REGISTRY_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'\n'
            f'echo -e "$GREEN Checking for GS Bucket: $BUCKET_NAME in project $PROJECT_ID $NC"\n'
            f'if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then\n'
            f'\n'
            f'  echo "Creating GS Bucket: ${LEFT_BRACKET}BUCKET_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gsutil mb -l ${LEFT_BRACKET}BUCKET_LOCATION{RIGHT_BRACKET} gs://$BUCKET_NAME\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "GS Bucket: ${LEFT_BRACKET}BUCKET_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'echo -e "$GREEN Checking for Service Account: $SERVICE_ACCOUNT_NAME in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud iam service-accounts list --project="$PROJECT_ID" | grep -E "(^|[[:blank:]])$SERVICE_ACCOUNT_FULL($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Service Account: ${LEFT_BRACKET}SERVICE_ACCOUNT_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \{NEWLINE}'
            f'      --description="For submitting PipelineJobs" \{NEWLINE}'
            f'      --display-name="Pipeline Runner Service Account"\n'
            f'else\n'
            f'\n'
            f'  echo "Service Account: ${LEFT_BRACKET}SERVICE_ACCOUNT_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n'
            f'\n'
            f'echo -e "$GREEN Updating required IAM roles in project $PROJECT_ID $NC"\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/aiplatform.user" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/artifactregistry.reader" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/bigquery.user" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'   --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'   --role="roles/bigquery.dataEditor" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/iam.serviceAccountUser" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/storage.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$SERVICE_ACCOUNT_FULL" \{NEWLINE}'
            f'    --role="roles/run.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/run.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/iam.serviceAccountUser" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/cloudtasks.enqueuer" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'gcloud projects add-iam-policy-binding $PROJECT_ID \{NEWLINE}'
            f'    --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \{NEWLINE}'
            f'    --role="roles/cloudscheduler.admin" \{NEWLINE}'
            f'    --no-user-output-enabled\n'
            f'\n'
            f'echo -e "$GREEN Checking for Cloud Source Repository: $CLOUD_SOURCE_REPO in project $PROJECT_ID $NC"\n'
            f'if ! (gcloud source repos list --project="$PROJECT_ID" | grep -E "(^|[[:blank:]])$CLOUD_SOURCE_REPO($|[[:blank:]])"); then\n'
            f'\n'
            f'  echo "Creating Cloud Source Repository: ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET} in project $PROJECT_ID"\n'
            f'  gcloud source repos create $CLOUD_SOURCE_REPO\n'
            f'\n'
            f'else\n'
            f'\n'
            f'  echo "Cloud Source Repository: ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
            f'\n'
            f'fi\n')
        if not self.run_local:
            create_resources_script += (
                f'\n'
                f'# Create cloud tasks queue\n'
                f'echo -e "$GREEN Checking for Cloud Tasks Queue: $CLOUD_TASKS_QUEUE_NAME in project $PROJECT_ID $NC"\n'
                f'if ! (gcloud tasks queues list --location $CLOUD_TASKS_QUEUE_LOCATION | grep -E "(^|[[:blank:]])$CLOUD_TASKS_QUEUE_NAME($|[[:blank:]])"); then\n'
                f'\n'
                f'  echo "Creating Cloud Tasks Queue: ${LEFT_BRACKET}CLOUD_TASKS_QUEUE_NAME{RIGHT_BRACKET} in project $PROJECT_ID"\n'
                f'  gcloud tasks queues create $CLOUD_TASKS_QUEUE_NAME \{NEWLINE}'
                f'  --location=$CLOUD_TASKS_QUEUE_LOCATION\n'
                f'\n'
                f'else\n'
                f'\n'
                f'  echo "Cloud Tasks Queue: ${LEFT_BRACKET}CLOUD_TASKS_QUEUE_NAME{RIGHT_BRACKET} already exists in project $PROJECT_ID"\n'
                f'\n'
                f'fi\n'
                f'\n'
                f'# Create cloud build trigger\n'
                f'echo -e "$GREEN Checking for Cloudbuild Trigger: $CB_TRIGGER_NAME in project $PROJECT_ID $NC"\n'
                f'if ! (gcloud beta builds triggers list --project="$PROJECT_ID" --region="$CB_TRIGGER_LOCATION" | grep -E "(^|[[:blank:]])name: $CB_TRIGGER_NAME($|[[:blank:]])"); then\n'
                f'\n'
                f'  echo "Creating Cloudbuild Trigger on branch $CLOUD_SOURCE_REPO_BRANCH in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
                f'  gcloud beta builds triggers create cloud-source-repositories \{NEWLINE}'
                f'  --region=$CB_TRIGGER_LOCATION \{NEWLINE}'
                f'  --name=$CB_TRIGGER_NAME \{NEWLINE}'
                f'  --repo=$CLOUD_SOURCE_REPO \{NEWLINE}'
                f'  --branch-pattern="$CLOUD_SOURCE_REPO_BRANCH" \{NEWLINE}'
                f'  --build-config={self.top_folder}cloudbuild.yaml\n'
                f'\n'
                f'else\n'
                f'\n'
                f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
                f'\n'
                f'fi\n') 
        return create_resources_script
    
    def _create_cloudbuild_config(self): 
        vpc_connector_tail = ''
        if self.vpc_connector != 'No VPC Specified':
            vpc_connector_tail = (
                f'\n'
                f'           "--ingress", "internal",\n'
                f'           "--vpc-connector", "{self.vpc_connector}",\n'
                f'           "--vpc-egress", "all-traffic"')
        vpc_connector_tail += ']\n'

        cloudbuild_comp_config = (BuilderUtils.LICENSE +
            f'steps:\n'
            f'# ==============================================================================\n'
            f'# BUILD & PUSH CUSTOM COMPONENT IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # build the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: [ "build", "-t", "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/components/component_base:latest", "." ]\n'''
            f'''    dir: "{self.top_folder}components/component_base"\n'''
            f'''    id: "build_component_base"\n'''
            f'''    waitFor: ["-"]\n'''
            f'\n'
            f'''  # push the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/components/component_base:latest"]\n'''
            f'''    dir: "{self.top_folder}components/component_base"\n'''
            f'''    id: "push_component_base"\n'''
            f'''    waitFor: ["build_component_base"]\n''')
        cloudbuild_cloudrun_config = (
            f'\n'
            f'# ==============================================================================\n'
            f'# BUILD & PUSH CLOUD RUN IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # build the run_pipeline image\n'''
            f'''  - name: 'gcr.io/cloud-builders/docker'\n'''
            f'''    args: [ "build", "-t", "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/run_pipeline:latest", "-f", "cloud_run/run_pipeline/Dockerfile", "." ]\n'''
            f'''    dir: "{self.top_folder}"\n'''
            f'''    id: "build_pipeline_runner_svc"\n'''
            f'''    waitFor: ['push_component_base']\n'''
            f'\n'
            f'''  # push the run_pipeline image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/run_pipeline:latest"]\n'''
            f'''    dir: "{self.top_folder}"\n'''
            f'''    id: "push_pipeline_runner_svc"\n'''
            f'''    waitFor: ["build_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # deploy the cloud run service\n'''
            f'''  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"\n'''
            f'''    entrypoint: gcloud\n'''
            f'''    args: ["run",\n'''
            f'''           "deploy",\n'''
            f'''           "{self.cloud_run_name}",\n'''
            f'''           "--image",\n'''
            f'''           "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/run_pipeline:latest",\n'''
            f'''           "--region",\n'''
            f'''           "{self.cloud_run_location}",\n'''
            f'''           "--service-account",\n'''
            f'''           "{self.pipeline_runner_service_account}",{vpc_connector_tail}'''
            f'''    id: "deploy_pipeline_runner_svc"\n'''
            f'''    waitFor: ["push_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # Copy runtime parameters\n'''
            f'''  - name: 'gcr.io/cloud-builders/gcloud'\n'''
            f'''    entrypoint: bash\n'''
            f'''    args:\n'''
            f'''      - '-e'\n'''
            f'''      - '-c'\n'''
            f'''      - |\n'''
            f'''        cp -r {self.top_folder}cloud_run/queueing_svc .\n'''
            f'''    id: "setup_queueing_svc"\n'''
            f'''    waitFor: ["deploy_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # Install dependencies\n'''
            f'''  - name: python\n'''
            f'''    entrypoint: pip\n'''
            f'''    args: ["install", "-r", "queueing_svc/requirements.txt", "--user"]\n'''
            f'''    id: "install_queueing_svc_deps"\n'''
            f'''    waitFor: ["setup_queueing_svc"]\n'''
            f'\n'
            f'''  # Submit to queue\n'''
            f'''  - name: python\n'''
            f'''    entrypoint: python\n'''
            f'''    args: ["queueing_svc/main.py", "--setting", "queue_job"]\n'''
            f'''    id: "submit_job_to_queue"\n'''
            f'''    waitFor: ["install_queueing_svc_deps"]\n''')
        cloudbuild_scheduler_config = (
            '\n'
            '''  # Create Scheduler Job\n'''
            '''  - name: python\n'''
            '''    entrypoint: python\n'''
            '''    args: ["queueing_svc/main.py", "--setting", "schedule_job"]\n'''
            '''    id: "schedule_job"\n'''
            '''    waitFor: ["submit_job_to_queue"]\n''')
        custom_comp_image = (
            f'\n'
            f'images:\n'
            f'''  # custom component images\n'''
            f'''  - "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/components/component_base:latest"\n''')
        cloudrun_image = (
            f'''  # Cloud Run image\n'''
            f'''  - "{self.af_registry_location}-docker.pkg.dev/{self.project_id}/{self.af_registry_name}/run_pipeline:latest"\n''')

        if self.run_local:
            cb_file_contents = cloudbuild_comp_config + custom_comp_image
        else:
            if self.cloud_schedule_pattern == 'No Schedule Specified':
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + custom_comp_image + cloudrun_image
            else:
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + cloudbuild_scheduler_config + custom_comp_image + cloudrun_image
        return cb_file_contents

class CloudRun():
    def __init__(self, defaults_file):
        """_summary_

        Args:
            defaults_file (_type_): _description_
        """
        self.left_bracket = '{'
        self.right_bracket = '}'
        
        defaults = BuilderUtils.read_yaml_file(defaults_file)
        self.project_id = defaults['gcp']['project_id']
        self.pipeline_runner_service_account = defaults['gcp']['pipeline_runner_service_account']
        self.cloud_tasks_queue_location = defaults['gcp']['cloud_tasks_queue_location']
        self.cloud_tasks_queue_name = defaults['gcp']['cloud_tasks_queue_name']
        self.cloud_run_name = defaults['gcp']['cloud_run_name']
        self.cloud_run_location = defaults['gcp']['cloud_run_location']
        self.cloud_schedule_pattern = defaults['gcp']['cloud_schedule_pattern']
        self.cloud_schedule_location = defaults['gcp']['cloud_schedule_location']
        self.cloud_schedule_name = defaults['gcp']['cloud_schedule_name']
        
        self.dockerfile = self._create_dockerfile()
        self.cloudrun_base_reqs = self._create_cloudrun_base_reqs()
        self.queueing_svc_reqs = self._create_queuing_svc_reqs()
        self.cloudrun_base = self._create_cloudrun_base()
        self.queueing_svc = self._create_queueing_svc()
        
    def _create_dockerfile(self):
        """Returns text for a Dockerfile that will be added to the cloudrun/run_pipeline directory.

        Returns:
            str: Dockerfile text.
        """
        return (
            BuilderUtils.LICENSE +
            'FROM python:3.9\n'
            '\n'
            '# Allow statements and log messages to immediately appear in the Knative logs\n'
            'ENV PYTHONUNBUFFERED True\n'
            '\n'
            '# Copy local code to the container image.\n'
            'ENV APP_HOME /app\n'
            'WORKDIR $APP_HOME\n'
            'COPY ./ ./\n'
            '\n'
            '# Upgrade pip\n'
            'RUN python -m pip install --upgrade pip\n'
            '# Install requirements\n'
            'RUN pip install --no-cache-dir -r /app/cloud_run/run_pipeline/requirements.txt\n'
            '# Compile pipeline spec\n'
            'RUN ./scripts/build_pipeline_spec.sh\n'
            '# Change Directories\n'
            'WORKDIR "/app/cloud_run/run_pipeline"\n'
            '# Run flask api server\n'
            'CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app\n'
        )
    
    def _create_cloudrun_base_reqs(self):
        """Returns the text of a cloudrun base requirements file to be written to the cloud_run/run_pipeline directory.

        Returns:
            str: Package requirements for cloudrun base
        """
        return (
            'kfp\n'
            'google-cloud-aiplatform\n'
            'google-cloud-pipeline-components\n'
            'Flask\n'
            'gunicorn\n'
            'pyyaml\n'
        )
    
    def _create_queuing_svc_reqs(self):
        """Returns the text of a queueing svc requirements file to be written to the cloud_run/queueing_svc directory.

        Returns:
            str: Package requirements for queueing svc.
        """
        return (
            'google-cloud\n'
            'google-cloud-tasks\n'
            'google-api-python-client\n'
            'google-cloud-run\n'
            'google-cloud-scheduler\n'
        )
    
    def _create_cloudrun_base(self):
        """Creates content for a main.py to be written to the cloud_run/run_pipeline
        directory. This file contains code for running a flask service that will act as 
        a pipeline runner service.

        Returns:
            str: Content of cloudrun main.py.
        """
        return (
            BuilderUtils.LICENSE +
            f'''"""Cloud Run to run pipeline spec"""\n'''
            f'''import logging\n'''
            f'''import os\n'''
            f'''from typing import Tuple\n'''
            f'\n'
            f'''import flask\n'''
            f'''from google.cloud import aiplatform\n'''
            f'''import yaml\n'''
            f'\n'
            f'''app = flask.Flask(__name__)\n'''
            f'\n'
            f'''logger = logging.getLogger()\n'''
            f'''log_level = os.environ.get('LOG_LEVEL', 'INFO')\n'''
            f'''logger.setLevel(log_level)\n'''
            f'\n'
            f'''CONFIG_FILE = '../../configs/defaults.yaml'\n'''
            f'''PIPELINE_SPEC_PATH_LOCAL = '../../scripts/pipeline_spec/pipeline_job.json'\n'''
            f'\n'
            f'''@app.route('/', methods=['POST'])\n'''
            f'''def process_request() -> flask.Response:\n'''
            f'''    """HTTP web service to trigger pipeline execution.\n'''
            f'\n'
            f'''    Returns:\n'''
            f'''        The response text, or any set of values that can be turned into a\n'''
            f'''        Response object using `make_response`\n'''
            f'''        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.\n'''
            f'''    """\n'''
            f'''    content_type = flask.request.headers['content-type']\n'''
            f'''    if content_type == 'application/json':\n'''
            f'''        request_json = flask.request.json\n'''
            f'\n'
            f'''        logging.debug('JSON Recieved:')\n'''
            f'''        logging.debug(request_json)\n'''
            f'\n'
            f'''        with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:\n'''
            f'''            config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
            f'\n'
            f'''        logging.debug('Calling run_pipeline()')\n'''
            f'''        dashboard_uri, resource_name = run_pipeline(\n'''
            f'''            project_id=config['gcp']['project_id'],\n'''
            f'''            pipeline_root=config['pipelines']['pipeline_storage_path'],\n'''
            f'''            pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],\n'''
            f'''            pipeline_params=request_json,\n'''
            f'''            pipeline_spec_path=PIPELINE_SPEC_PATH_LOCAL)\n'''
            f'''        return flask.make_response({LEFT_BRACKET}\n'''
            f'''            'dashboard_uri': dashboard_uri,\n'''
            f'''            'resource_name': resource_name\n'''
            f'''        {RIGHT_BRACKET}, 200)\n'''
            f'\n'
            f'''    else:\n'''
            f'''        raise ValueError(f'Unknown content type: {LEFT_BRACKET}content_type{RIGHT_BRACKET}')\n'''
            f'\n'
            f'''def run_pipeline(\n'''
            f'''    project_id: str,\n'''
            f'''    pipeline_root: str,\n'''
            f'''    pipeline_runner_sa: str,\n'''
            f'''    pipeline_params: dict,\n'''
            f'''    pipeline_spec_path: str,\n'''
            f'''    display_name: str = 'mlops-pipeline-run',\n'''
            f'''    enable_caching: bool = False) -> Tuple[str, str]:\n'''
            f'''    """Executes a pipeline run.\n'''
            f'\n'
            f'''    Args:\n'''
            f'''        project_id: The project_id.\n'''
            f'''        pipeline_root: GCS location of the pipeline runs metadata.\n'''
            f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
            f'''        pipeline_params: Pipeline parameters values.\n'''
            f'''        pipeline_spec_path: Location of the pipeline spec JSON.\n'''
            f'''        display_name: Name to call the pipeline.\n'''
            f'''        enable_caching: Should caching be enabled (Boolean)\n'''
            f'''    """\n'''
            f'''    logging.debug('Pipeline Parms Configured:')\n'''
            f'''    logging.debug(pipeline_params)\n'''
            f'\n'
            f'''    aiplatform.init(project=project_id)\n'''
            f'''    job = aiplatform.PipelineJob(\n'''
            f'''        display_name = display_name,\n'''
            f'''        template_path = pipeline_spec_path,\n'''
            f'''        pipeline_root = pipeline_root,\n'''
            f'''        parameter_values = pipeline_params,\n'''
            f'''        enable_caching = enable_caching)\n'''
            f'''    logging.debug('AI Platform job built. Submitting...')\n'''
            f'''    job.submit(service_account=pipeline_runner_sa)\n'''
            f'''    logging.debug('Job sent!')\n'''
            f'''    dashboard_uri = job._dashboard_uri()\n'''
            f'''    resource_name = job.resource_name\n'''
            f'''    return dashboard_uri, resource_name\n'''
            f'\n'
            f'''if __name__ == '__main__':\n'''
            f'''    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))\n'''
        )
        
    def _create_queueing_svc(self):
        """Creates content for a main.py to be written to the cloud_run/queueing_svc 
        directory. This file contains code for submitting a job to the cloud runner
        service, and creating a cloud scheduler job.

        Returns:
            str: Content of queueing svc main.py.
        """
        return (
            BuilderUtils.LICENSE +
            f'''"""Submit pipeline job using Cloud Tasks and create Cloud Scheduler Job."""\n'''
            f'''import argparse\n'''
            f'''import json\n'''
            f'\n'
            f'''from google.cloud import run_v2\n'''
            f'''from google.cloud import scheduler_v1\n'''
            f'''from google.cloud import tasks_v2\n'''
            f'\n'
            f'''CLOUD_RUN_LOCATION = '{self.cloud_run_location}'\n'''
            f'''CLOUD_RUN_NAME = '{self.cloud_run_name}'\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION = '{self.cloud_tasks_queue_location}'\n'''
            f'''CLOUD_TASKS_QUEUE_NAME = '{self.cloud_tasks_queue_name}'\n'''
            f'''PARAMETER_VALUES_PATH = 'queueing_svc/pipeline_parameter_values.json'\n'''
            f'''PIPELINE_RUNNER_SA = '{self.pipeline_runner_service_account}'\n'''
            f'''PROJECT_ID = '{self.project_id}'\n'''
            f'''SCHEDULE_LOCATION = '{self.cloud_schedule_location}'\n'''
            f'''SCHEDULE_PATTERN = '{self.cloud_schedule_pattern}'\n'''
            f'''SCHEDULE_NAME = '{self.cloud_schedule_name}'\n'''
            f'\n'
            f'''def get_runner_svc_uri(\n'''
            f'''    cloud_run_location: str,\n'''
            f'''    cloud_run_name: str,\n'''
            f'''    project_id: str):\n'''
            f'''    """Fetches the uri for the given cloud run instance.\n'''
            f'\n'
            f'''    Args:\n'''
            f'''        cloud_run_location: The location of the cloud runner service.\n'''
            f'''        cloud_run_name: The name of the cloud runner service.\n'''
            f'''        project_id: The project ID.\n'''
            f'''    Returns:\n'''
            f'''        str: Uri of the Cloud Run instance.\n'''
            f'''    """\n'''
            f'''    client = run_v2.ServicesClient()\n'''
            f'''    parent = client.service_path(project_id, cloud_run_location, cloud_run_name)\n'''
            f'''    request = run_v2.GetServiceRequest(name=parent)\n'''
            f'''    response = client.get_service(request=request)\n'''
            f'''    return response.uri\n'''
            f'\n'
            f'''def get_json_bytes(file_path: str):\n'''
            f'''    """Reads a json file at the specified path and returns as bytes.\n'''
            f'\n'
            f'''    Args:\n'''
            f'''        file_path: Path of the json file.\n'''
            f'''    Returns:\n'''
            f'''        bytes: Encode bytes of the file.\n'''
            f'''    """\n'''
            f'''    try:\n'''
            f'''        with open(file_path, 'r', encoding='utf-8') as file:\n'''
            f'''            data = json.load(file)\n'''
            f'''        file.close()\n'''
            f'''    except OSError as err:\n'''
            f'''        raise Exception(f'Error reading json file. {LEFT_BRACKET}err{RIGHT_BRACKET}') from err\n'''
            f'''    return json.dumps(data).encode()\n'''
            f'\n'
            f'''def create_cloud_task(\n'''
            f'''    cloud_tasks_queue_location: str,\n'''
            f'''    cloud_tasks_queue_name: str,\n'''
            f'''    parameter_values_path: str,\n'''
            f'''    pipeline_runner_sa: str,\n'''
            f'''    project_id: str,\n'''
            f'''    runner_svc_uri: str):\n'''
            f'''    """Create a task to the queue with the runtime parameters.\n'''
            f'\n'
            f'''    Args:\n'''
            f'''        cloud_run_location: The location of the cloud runner service.\n'''
            f'''        cloud_run_name: The name of the cloud runner service.\n'''
            f'''        cloud_tasks_queue_location: The location of the cloud tasks queue.\n'''
            f'''        cloud_tasks_queue_name: The name of the cloud tasks queue.\n'''
            f'''        parameter_values_path: Path to json pipeline params.\n'''
            f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
            f'''        project_id: The project ID.\n'''
            f'''        runner_svc_uri: Uri of the Cloud Run instance.\n'''
            f'''    """\n'''
            f'''    client = tasks_v2.CloudTasksClient()\n'''
            f'''    parent = client.queue_path(project_id, cloud_tasks_queue_location, cloud_tasks_queue_name)\n'''
            f'''    task = {LEFT_BRACKET}\n'''
            f'''        'http_request': {LEFT_BRACKET}\n'''
            f'''            'http_method': tasks_v2.HttpMethod.POST,\n'''
            f'''            'url': runner_svc_uri,\n'''
            f'''            'oidc_token': {LEFT_BRACKET}\n'''
            f'''                'service_account_email': pipeline_runner_sa,\n'''
            f'''                'audience': runner_svc_uri\n'''
            f'''            {RIGHT_BRACKET},\n'''
            f'''            'headers': {LEFT_BRACKET}\n'''
            f'''               'Content-Type': 'application/json'\n'''
            f'''            {RIGHT_BRACKET}\n'''
            f'''        {RIGHT_BRACKET}\n'''
            f'''    {RIGHT_BRACKET}\n'''
            f'''    task['http_request']['body'] = get_json_bytes(parameter_values_path)\n'''
            f'''    response = client.create_task(request={LEFT_BRACKET}'parent': parent, 'task': task{RIGHT_BRACKET})\n'''
            f'''    print(f'Created task {LEFT_BRACKET}response.name{RIGHT_BRACKET}')\n'''
            f'\n'
            f'''def create_cloud_scheduler_job(\n'''
            f'''    parameter_values_path: str,\n'''
            f'''    pipeline_runner_sa: str,\n'''
            f'''    project_id: str,\n'''
            f'''    runner_svc_uri: str,\n'''
            f'''    schedule_location: str,\n'''
            f'''    schedule_name: str,\n'''
            f'''    schedule_pattern: str):\n'''
            f'''    """Creates a scheduled pipeline job.\n'''
            f'\n'
            f'''    Args:\n'''
            f'''        parameter_values_path: Path to json pipeline params.\n'''
            f'''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
            f'''        project_id: The project ID.\n'''
            f'''        runner_svc_uri: Uri of the Cloud Run instance.\n'''
            f'''        schedule_location: The location of the scheduler resource.\n'''
            f'''        schedule_name: The name of the scheduler resource.\n'''
            f'''        schedule_pattern: Cron formatted value used to create a Scheduled retrain job.\n'''
            f'''    """\n'''
            f'''    client = scheduler_v1.CloudSchedulerClient()\n'''
            f'''    parent = f'projects/{LEFT_BRACKET}project_id{RIGHT_BRACKET}/locations/{LEFT_BRACKET}schedule_location{RIGHT_BRACKET}'\n'''
            f'''    name = f'{LEFT_BRACKET}parent{RIGHT_BRACKET}/jobs/{LEFT_BRACKET}schedule_name{RIGHT_BRACKET}'\n'''
            f'\n'
            f'''    request = scheduler_v1.ListJobsRequest(parent=parent)\n'''
            f'''    page_result = client.list_jobs(request=request)\n'''
            f'''    for response in page_result:\n'''
            f'''        if response.name == name:\n'''
            f'''            print(f'Cloud Scheduler {LEFT_BRACKET}schedule_name{RIGHT_BRACKET} resource already exists in '\n'''
            f'''                  f'project {LEFT_BRACKET}project_id{RIGHT_BRACKET}.')\n'''
            f'''            return\n'''
            f'\n'
            f'''    oidc_token = scheduler_v1.OidcToken(\n'''
            f'''        service_account_email=pipeline_runner_sa,\n'''
            f'''        audience=runner_svc_uri)\n'''
            f'\n'
            f'''    target = scheduler_v1.HttpTarget(\n'''
            f'''       uri=runner_svc_uri,\n'''
            f'''        http_method=scheduler_v1.HttpMethod(1), # HTTP POST\n'''
            f'''        headers={LEFT_BRACKET}'Content-Type': 'application/json'{RIGHT_BRACKET},\n'''
            f'''        body=get_json_bytes(parameter_values_path),\n'''
            f'''        oidc_token=oidc_token)\n'''
            f'\n'
            f'''    job = scheduler_v1.Job(\n'''
            f'''       name=f'{LEFT_BRACKET}parent{RIGHT_BRACKET}/jobs/{LEFT_BRACKET}schedule_name{RIGHT_BRACKET}',\n'''
            f'''        description='AutoMLOps cloud scheduled run.',\n'''
            f'''        http_target=target,\n'''
            f'''        schedule=schedule_pattern)\n'''
            f'\n'
            f'''    request = scheduler_v1.CreateJobRequest(\n'''
            f'''        parent=parent,\n'''
            f'''        job=job)\n'''
            f'\n'
            f'''    response = client.create_job(request=request)\n'''
            f'''    print(response)\n'''
            f'\n'
            f'''if __name__ == '__main__':\n'''
            f'''    parser = argparse.ArgumentParser()\n'''
            f'''    parser.add_argument('--setting', type=str,\n'''
            f'''                       help='The config file for setting default values.')\n'''
            f'''    args = parser.parse_args()\n'''
            f'\n'
            f'''    uri = get_runner_svc_uri(\n'''
            f'''        cloud_run_location=CLOUD_RUN_LOCATION,\n'''
            f'''        cloud_run_name=CLOUD_RUN_NAME,\n'''
            f'''        project_id=PROJECT_ID)\n'''
            f'\n'
            f'''    if args.setting == 'queue_job':\n'''
            f'''        create_cloud_task(\n'''
            f'''            cloud_tasks_queue_location=CLOUD_TASKS_QUEUE_LOCATION,\n'''
            f'''            cloud_tasks_queue_name=CLOUD_TASKS_QUEUE_NAME,\n'''
            f'''            parameter_values_path=PARAMETER_VALUES_PATH,\n'''
            f'''            pipeline_runner_sa=PIPELINE_RUNNER_SA,\n'''
            f'''            project_id=PROJECT_ID,\n'''
            f'''            runner_svc_uri=uri)\n'''
            f'\n'
            f'''    if args.setting == 'schedule_job':\n'''
            f'''        create_cloud_scheduler_job(\n'''
            f'''            parameter_values_path=PARAMETER_VALUES_PATH,\n'''
            f'''            pipeline_runner_sa=PIPELINE_RUNNER_SA,\n'''
            f'''            project_id=PROJECT_ID,\n'''
            f'''            runner_svc_uri=uri,\n'''
            f'''            schedule_location=SCHEDULE_LOCATION,\n'''
            f'''            schedule_name=SCHEDULE_NAME,\n'''
            f'''            schedule_pattern=SCHEDULE_PATTERN)\n''')
    

if __name__ == "__main__":
    print('Test')