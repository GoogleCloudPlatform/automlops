from AutoMLOps import BuilderUtils

from typing import Callable, Dict, List, Optional

LEFT_BRACKET = '{'
RIGHT_BRACKET = '}'
NEWLINE = '\n'

class AutoMLOps():

    def __init__(self,
                 af_registry_location: str,
                 af_registry_name: str,
                 cb_trigger_location: str,
                 cb_trigger_name: str,
                 cloud_run_location: str,
                 cloud_run_name: str,
                 cloud_tasks_queue_location: str,
                 cloud_tasks_queue_name: str,
                 csr_branch_name: str,
                 csr_name: str,
                 gs_bucket_location: str,
                 gs_bucket_name: str,
                 image: str,
                 pipeline_runner_sa: str,
                 project_id: str,
                 run_local: str,
                 schedule_location: str,
                 schedule_name: str,
                 schedule_pattern: str,
                 top_folder: str,
                 vpc_connector: str):
        """Instantiate AutoMLOps scripts object with all necessary attributes.

        Args:
            af_registry_location: Region of the Artifact Registry.
            af_registry_name: Artifact Registry name where components are stored.
            cb_trigger_location: The location of the cloudbuild trigger.
            cb_trigger_name: The name of the cloudbuild trigger.
            cloud_run_location: The location of the cloud runner service.
            cloud_run_name: The name of the cloud runner service.
            cloud_tasks_queue_location: The location of the cloud tasks queue.
            cloud_tasks_queue_name: The name of the cloud tasks queue.
            csr_branch_name: The name of the csr branch to push to to trigger cb job.
            csr_name: The name of the cloud source repo to use.
            gs_bucket_location: Region of the GS bucket.
            gs_bucket_name: GS bucket name where pipeline run metadata is stored.
            pipeline_runner_sa: Service Account to runner PipelineJobs.
            project_id: The project ID.
            run_local (_type_): _description_
            schedule_location: The location of the scheduler resource.
            schedule_name: The name of the scheduler resource.
            schedule_pattern: Cron formatted value used to create a Scheduled retrain job.
            top_folder (_type_): _description_
            vpc_connector: The name of the vpc connector to use.
        """

        # Set passed variables as hidden attributes
        self.__top_folder = top_folder
        self.__run_local = run_local

        # Parse defaults file for hidden class attributes
        self.__af_registry_name = af_registry_name
        self.__af_registry_location = af_registry_location
        self.__project_id = project_id
        self.__gs_bucket_name = gs_bucket_name
        self.__gs_bucket_location = gs_bucket_location
        self.__pipeline_region = gs_bucket_location
        self.__pipeline_runner_service_account = pipeline_runner_sa
        self.__cloud_source_repository = csr_name
        self.__cloud_source_repository_branch = csr_branch_name
        self.__cb_trigger_location = cb_trigger_location
        self.__cb_trigger_name = cb_trigger_name
        self.__cloud_tasks_queue_location = cloud_tasks_queue_location
        self.__cloud_tasks_queue_name = cloud_tasks_queue_name
        self.__vpc_connector = vpc_connector
        self.__cloud_run_name = cloud_run_name
        self.__cloud_run_location = cloud_run_location
        self.__cloud_schedule_location = schedule_location
        self.__cloud_schedule_name = schedule_name
        self.__cloud_schedule_pattern = schedule_pattern
        self.__image = image

        # Set generated scripts as public attributes
        self.build_pipeline_spec = self._build_pipeline_spec()
        self.build_components = self._build_components()
        self.run_pipeline = self._run_pipeline()
        self.run_all = self._run_all()
        self.create_resources_script = self._create_resources_script()
        self.create_cloudbuild_config = self._create_cloudbuild_config()
        self.dockerfile = self._create_dockerfile()
        self.defaults = self._create_default_config()
        
    def _build_pipeline_spec(self):
        """Builds content of a shell script to build the pipeline specs.

        Returns:
            str: Text of script to build pipeline specs.
        """
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Builds the pipeline specs\n'
            f'# This script should run from the {self.__top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline --config $CONFIG_FILE\n')

    def _build_components(self):
        """Builds content of a shell script to build components.

        Returns:
            str: Text of script to build components.
        """
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Submits a Cloud Build job that builds and deploys the components\n'
            f'# This script should run from the {self.__top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'gcloud builds submit .. --config cloudbuild.yaml --timeout=3600\n')

    def _run_pipeline(self):
        """Builds content of a shell script to run the pipeline.

        Returns:
            str: Text of script to run pipeline.
        """
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Submits the PipelineJob to Vertex AI\n'
            f'# This script should run from the {self.__top_folder} directory\n'
            '# Change directory in case this is not the script root.\n'
            '\n'
            'CONFIG_FILE=configs/defaults.yaml\n'
            '\n'
            'python3 -m pipelines.pipeline_runner --config $CONFIG_FILE\n')

    def _run_all(self):
        """Builds content of a shell script to run all other shell scripts.

        Returns:
            str: Text of script to run all other scripts.
        """
        return (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            '# Builds components, pipeline specs, and submits the PipelineJob.\n'
            f'# This script should run from the {self.__top_folder} directory\n'
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
        """Builds content of create_resources.sh, which creates a specified
        artifact registry and gs bucket if they do not already exist. Also creates
        a service account to run Vertex AI Pipelines.

        Returns:
            str: Text to be written to create_resources.sh
        """
        create_resources_script = (
            '#!/bin/bash\n' + BuilderUtils.LICENSE +
            f'# This script will create an artifact registry and gs bucket if they do not already exist.\n'
            f'\n'
            f'''GREEN='\033[0;32m'\n'''
            f'''NC='\033[0m'\n'''
            f'''AF_REGISTRY_NAME={self.__af_registry_name}\n'''
            f'''AF_REGISTRY_LOCATION={self.__af_registry_location}\n'''
            f'''PROJECT_ID={self.__project_id}\n'''
            f'''PROJECT_NUMBER=`gcloud projects describe {self.__project_id} --format 'value(projectNumber)'`\n'''
            f'''BUCKET_NAME={self.__gs_bucket_name}\n'''
            f'''BUCKET_LOCATION={self.__pipeline_region}\n'''
            f'''SERVICE_ACCOUNT_NAME={self.__pipeline_runner_service_account.split('@')[0]}\n'''
            f'''SERVICE_ACCOUNT_FULL={self.__pipeline_runner_service_account}\n'''
            f'''CLOUD_SOURCE_REPO={self.__cloud_source_repository}\n'''
            f'''CLOUD_SOURCE_REPO_BRANCH={self.__cloud_source_repository_branch}\n'''
            f'''CB_TRIGGER_LOCATION={self.__cb_trigger_location}\n'''
            f'''CB_TRIGGER_NAME={self.__cb_trigger_name}\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION={self.__cloud_tasks_queue_location}\n'''
            f'''CLOUD_TASKS_QUEUE_NAME={self.__cloud_tasks_queue_name}\n'''
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

        if not self.__run_local:
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
                f'  --build-config={self.__top_folder}cloudbuild.yaml\n'
                f'\n'
                f'else\n'
                f'\n'
                f'  echo "Cloudbuild Trigger already exists in project $PROJECT_ID for repo ${LEFT_BRACKET}CLOUD_SOURCE_REPO{RIGHT_BRACKET}"\n'
                f'\n'
                f'fi\n')

        return create_resources_script

    def _create_cloudbuild_config(self): 
        """Builds the content of cloudbuild.yaml.

        Args:
            str: Text content of cloudbuild.yaml.
        """
        vpc_connector_tail = ''
        if self.__vpc_connector != 'No VPC Specified':
            vpc_connector_tail = (
                f'\n'
                f'           "--ingress", "internal",\n'
                f'           "--vpc-connector", "{self.__vpc_connector}",\n'
                f'           "--vpc-egress", "all-traffic"')
        vpc_connector_tail += ']\n'

        cloudbuild_comp_config = (
            BuilderUtils.LICENSE +
            f'steps:\n'
            f'# ==============================================================================\n'
            f'# BUILD CUSTOM IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # build the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: [ "build", "-t", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest", "." ]\n'''
            f'''    dir: "{self.__top_folder}components/component_base"\n'''
            f'''    id: "build_component_base"\n'''
            f'''    waitFor: ["-"]\n'''
            f'\n'
            f'''  # build the run_pipeline image\n'''
            f'''  - name: 'gcr.io/cloud-builders/docker'\n'''
            f'''    args: [ "build", "-t", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest", "-f", "cloud_run/run_pipeline/Dockerfile", "." ]\n'''
            f'''    dir: "{self.__top_folder}"\n'''
            f'''    id: "build_pipeline_runner_svc"\n'''
            f'''    waitFor: ['build_component_base']\n''')

        cloudbuild_cloudrun_config = (
            f'\n'
            f'# ==============================================================================\n'
            f'# PUSH & DEPLOY CUSTOM IMAGES\n'
            f'# ==============================================================================\n'
            f'\n'
            f'''  # push the component_base image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest"]\n'''
            f'''    dir: "{self.__top_folder}components/component_base"\n'''
            f'''    id: "push_component_base"\n'''
            f'''    waitFor: ["build_pipeline_runner_svc"]\n'''
            f'\n'
            f'''  # push the run_pipeline image\n'''
            f'''  - name: "gcr.io/cloud-builders/docker"\n'''
            f'''    args: ["push", "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest"]\n'''
            f'''    dir: "{self.__top_folder}"\n'''
            f'''    id: "push_pipeline_runner_svc"\n'''
            f'''    waitFor: ["push_component_base"]\n'''
            f'\n'
            f'''  # deploy the cloud run service\n'''
            f'''  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"\n'''
            f'''    entrypoint: gcloud\n'''
            f'''    args: ["run",\n'''
            f'''           "deploy",\n'''
            f'''           "{self.__cloud_run_name}",\n'''
            f'''           "--image",\n'''
            f'''           "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest",\n'''
            f'''           "--region",\n'''
            f'''           "{self.__cloud_run_location}",\n'''
            f'''           "--service-account",\n'''
            f'''           "{self.__pipeline_runner_service_account}",{vpc_connector_tail}'''
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
            f'''        cp -r {self.__top_folder}cloud_run/queueing_svc .\n'''
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
            f'''  - "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/components/component_base:latest"\n''')

        cloudrun_image = (
            f'''  # Cloud Run image\n'''
            f'''  - "{self.__af_registry_location}-docker.pkg.dev/{self.__project_id}/{self.__af_registry_name}/run_pipeline:latest"\n''')

        if self.__run_local:
            cb_file_contents = cloudbuild_comp_config + custom_comp_image
        else:
            if self.__cloud_schedule_pattern == 'No Schedule Specified':
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + custom_comp_image + cloudrun_image
            else:
                cb_file_contents = cloudbuild_comp_config + cloudbuild_cloudrun_config + cloudbuild_scheduler_config + custom_comp_image + cloudrun_image

        return cb_file_contents

    def _create_dockerfile(self):
        """Creates the content of a Dockerfile to be written to the component_base directory.

        Args:
            default_image: Default image used for this process.

        Returns:
            str: Text content of dockerfile.
        """
        return (
            BuilderUtils.LICENSE +
            f'FROM {self.__image}\n'
            f'RUN python -m pip install --upgrade pip\n'
            f'COPY requirements.txt .\n'
            f'RUN python -m pip install -r \ \n'
            f'    requirements.txt --quiet --no-cache-dir \ \n'
            f'    && rm -f requirements.txt\n'
            f'COPY ./src /pipelines/component/src\n'
            f'ENTRYPOINT ["/bin/bash"]\n')
        
    def _create_default_config(self):
        """Creates default defaults.yaml file contents. This defaults
        file is used by subsequent functions and by the pipeline
        files themselves.

        Returns:
            str: Defaults yaml file content
        """
        return (
            BuilderUtils.LICENSE +
            f'# These values are descriptive only - do not change.\n'
            f'# Rerun AutoMLOps.generate() to change these values.\n'
            f'gcp:\n'
            f'  af_registry_location: {self.__af_registry_location}\n'
            f'  af_registry_name: {self.__af_registry_name}\n'
            f'  cb_trigger_location: {self.__cb_trigger_location}\n'
            f'  cb_trigger_name: {self.__cb_trigger_name}\n'
            f'  cloud_run_location: {self.__cloud_run_location}\n'
            f'  cloud_run_name: {self.__cloud_run_name}\n'
            f'  cloud_tasks_queue_location: {self.__cloud_tasks_queue_location}\n'
            f'  cloud_tasks_queue_name: {self.__cloud_tasks_queue_name}\n'
            f'  cloud_schedule_location: {self.__cloud_schedule_location}\n'
            f'  cloud_schedule_name: {self.__cloud_schedule_name}\n'
            f'  cloud_schedule_pattern: {self.__cloud_schedule_pattern}\n'
            f'  cloud_source_repository: {self.__cloud_source_repository}\n'
            f'  cloud_source_repository_branch: {self.__cloud_source_repository_branch}\n'
            f'  gs_bucket_name: {self.__gs_bucket_name}\n'
            f'  pipeline_runner_service_account: {self.__pipeline_runner_service_account}\n'
            f'  project_id: {self.__project_id}\n'
            f'  vpc_connector: {self.__vpc_connector}\n'
            f'\n'
            f'pipelines:\n'
            f'  parameter_values_path: {BuilderUtils.PARAMETER_VALUES_PATH}\n'
            f'  pipeline_component_directory: components\n'
            f'  pipeline_job_spec_path: {BuilderUtils.PIPELINE_JOB_SPEC_PATH}\n'
            f'  pipeline_region: {self.__gs_bucket_location}\n'
            f'  pipeline_storage_path: gs://{self.__gs_bucket_name}/pipeline_root\n')

class CloudRun():
    def __init__(self, defaults_file):
        """_summary_

        Args:
            defaults_file (_type_): _description_
        """

        # Parse defaults file for hidden class attributes
        defaults = BuilderUtils.read_yaml_file(defaults_file)
        self.__project_id = defaults['gcp']['project_id']
        self.__pipeline_runner_service_account = defaults['gcp']['pipeline_runner_service_account']
        self.__cloud_tasks_queue_location = defaults['gcp']['cloud_tasks_queue_location']
        self.__cloud_tasks_queue_name = defaults['gcp']['cloud_tasks_queue_name']
        self.__cloud_run_name = defaults['gcp']['cloud_run_name']
        self.__cloud_run_location = defaults['gcp']['cloud_run_location']
        self.__cloud_schedule_pattern = defaults['gcp']['cloud_schedule_pattern']
        self.__cloud_schedule_location = defaults['gcp']['cloud_schedule_location']
        self.__cloud_schedule_name = defaults['gcp']['cloud_schedule_name']

        # Set generated scripts as public attributes
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
            'FROM python:3.9-slim\n'
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
            str: Package requirements for cloudrun base.
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
            f'''CLOUD_RUN_LOCATION = '{self.__cloud_run_location}'\n'''
            f'''CLOUD_RUN_NAME = '{self.__cloud_run_name}'\n'''
            f'''CLOUD_TASKS_QUEUE_LOCATION = '{self.__cloud_tasks_queue_location}'\n'''
            f'''CLOUD_TASKS_QUEUE_NAME = '{self.__cloud_tasks_queue_name}'\n'''
            f'''PARAMETER_VALUES_PATH = 'queueing_svc/pipeline_parameter_values.json'\n'''
            f'''PIPELINE_RUNNER_SA = '{self.__pipeline_runner_service_account}'\n'''
            f'''PROJECT_ID = '{self.__project_id}'\n'''
            f'''SCHEDULE_LOCATION = '{self.__cloud_schedule_location}'\n'''
            f'''SCHEDULE_PATTERN = '{self.__cloud_schedule_pattern}'\n'''
            f'''SCHEDULE_NAME = '{self.__cloud_schedule_name}'\n'''
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

class Component():
    def __init__(self, component_spec, defaults_file):
        self.__component_spec = component_spec
        
        # Parse defaults file for hidden class attributes
        defaults = BuilderUtils.read_yaml_file(defaults_file)
        self.__af_registry_location = defaults['gcp']['af_registry_location']
        self.__project_id = defaults['gcp']['project_id']
        self.__af_registry_name = defaults['gcp']['af_registry_name']
        
        self.task = self._create_task()
        self.compspec_image = self._create_compspec_image()
        
    def _create_task(self):
        """Creates the content of the cell python code to be written to a file with required imports.

        Returns:
            str: Contents of component base source code.
        """
        custom_code = self.__component_spec['implementation']['container']['command'][-1]
        default_imports = (
            BuilderUtils.LICENSE +
            'import argparse\n'
            'import json\n'
            'import kfp\n'
            'from kfp.v2 import dsl\n'
            'from kfp.v2.components import executor\n'
            'from kfp.v2.dsl import *\n'
            'from typing import *\n'
            '\n')
        main_func = (
            '\n'
            '''def main():\n'''
            '''    """Main executor."""\n'''
            '''    parser = argparse.ArgumentParser()\n'''
            '''    parser.add_argument('--executor_input', type=str)\n'''
            '''    parser.add_argument('--function_to_execute', type=str)\n'''
            '\n'
            '''    args, _ = parser.parse_known_args()\n'''
            '''    executor_input = json.loads(args.executor_input)\n'''
            '''    function_to_execute = globals()[args.function_to_execute]\n'''
            '\n'
            '''    executor.Executor(\n'''
            '''        executor_input=executor_input,\n'''
            '''        function_to_execute=function_to_execute).execute()\n'''
            '\n'
            '''if __name__ == '__main__':\n'''
            '''    main()\n''')
        return default_imports + custom_code + main_func
    
    def _create_compspec_image(self):
        """Write the correct image for the component spec.

        Returns:
            str: Component spec image.
        """
        return (
            f'''{self.__af_registry_location}-docker.pkg.dev/'''
            f'''{self.__project_id}/'''
            f'''{self.__af_registry_name}/'''
            f'''components/component_base:latest''')
        
class Pipeline():
    def __init__(self, custom_training_job_specs, defaults_file):
        """_summary_

        Args:
            custom_training_job_specs (List[Dict]): custom_training_job_specs: Specifies the specs to run the training job with.
            defaults_file (_type_): _description_
        """
        self.__custom_training_job_specs = custom_training_job_specs
        
        defaults = BuilderUtils.read_yaml_file(defaults_file)
        self.__project_id = defaults['gcp']['project_id']

        self.pipeline_imports = self._get_pipeline_imports()
        self.pipeline_argparse = self._get_pipeline_argparse()
        self.pipeline_runner = self._get_pipeline_runner()
    
    def _get_pipeline_imports(self):
        """Generates python code that imports modules and loads all custom components.

        Returns:
            str: Python pipeline_imports code.
        """
        components_list = BuilderUtils.get_components_list(full_path=False)
        gcpc_imports = (
            'from functools import partial\n'
            'from google_cloud_pipeline_components.v1.custom_job import create_custom_training_job_op_from_component\n')
        quote = '\''
        newline_tab = '\n    '

        # If there is a custom training job specified, write those to feed to pipeline imports
        if not self.__custom_training_job_specs:
            custom_specs = ''
        else:
            custom_specs = (
                f'''    {newline_tab.join(f'{spec["component_spec"]}_custom_training_job_specs = {BuilderUtils.format_spec_dict(spec)}' for spec in self.__custom_training_job_specscustom_training_job_specs)}'''
                f'\n'
                f'''    {newline_tab.join(f'{spec["component_spec"]}_job_op = create_custom_training_job_op_from_component(**{spec["component_spec"]}_custom_training_job_specs)' for spec in self.__custom_training_job_specs)}'''
                f'\n'
                f'''    {newline_tab.join(f'{spec["component_spec"]} = partial({spec["component_spec"]}_job_op, project={quote}{self.__project_id}{quote})' for spec in self.__custom_training_job_specs)}'''        
                f'\n')

        # Return standard code and customized specs
        return (
            f'''import argparse\n'''
            f'''import os\n'''
            f'''{gcpc_imports if self.__custom_training_job_specs else ''}'''
            f'''import kfp\n'''
            f'''from kfp.v2 import compiler, dsl\n'''
            f'''from kfp.v2.dsl import *\n'''
            f'''from typing import *\n'''
            f'''import yaml\n'''
            f'\n'
            f'''def load_custom_component(component_name: str):\n'''
            f'''    component_path = os.path.join('components',\n'''
            f'''                                component_name,\n'''
            f'''                              'component.yaml')\n'''
            f'''    return kfp.components.load_component_from_file(component_path)\n'''
            f'\n'
            f'''def create_training_pipeline(pipeline_job_spec_path: str):\n'''
            f'''    {newline_tab.join(f'{component} = load_custom_component(component_name={quote}{component}{quote})' for component in components_list)}\n'''
            f'\n'
            f'''{custom_specs}''')
        
    def _get_pipeline_argparse(self):
        """Generates python code that loads default pipeline parameters from the defaults config_file.

        Returns:
            str: Python pipeline_argparse code.
        """
        return (
            '''if __name__ == '__main__':\n'''
            '''    parser = argparse.ArgumentParser()\n'''
            '''    parser.add_argument('--config', type=str,\n'''
            '''                       help='The config file for setting default values.')\n'''
            '\n'
            '''    args = parser.parse_args()\n'''
            '\n'
            '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
            '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
            '\n'
            '''    pipeline = create_training_pipeline(\n'''
            '''        pipeline_job_spec_path=config['pipelines']['pipeline_job_spec_path'])\n''')

    def _get_pipeline_runner(self):
        """Generates python code that sends a PipelineJob to Vertex AI.

        Returns:
            str: Python pipeline_runner code.
        """
        return (BuilderUtils.LICENSE +
            '''import argparse\n'''
            '''import json\n'''
            '''import logging\n'''
            '''import os\n'''
            '''import yaml\n'''
            '\n'
            '''from google.cloud import aiplatform\n'''
            '\n'
            '''logger = logging.getLogger()\n'''
            '''log_level = os.environ.get('LOG_LEVEL', 'INFO')\n'''
            '''logger.setLevel(log_level)\n'''
            '\n'
            '''def run_pipeline(\n'''
            '''    project_id: str,\n'''
            '''    pipeline_root: str,\n'''
            '''    pipeline_runner_sa: str,\n'''
            '''    parameter_values_path: str,\n'''
            '''    pipeline_spec_path: str,\n'''
            '''    display_name: str = 'mlops-pipeline-run',\n'''
            '''    enable_caching: bool = False):\n'''
            '''    """Executes a pipeline run.\n'''
            '\n'
            '''    Args:\n'''
            '''        project_id: The project_id.\n'''
            '''        pipeline_root: GCS location of the pipeline runs metadata.\n'''
            '''        pipeline_runner_sa: Service Account to runner PipelineJobs.\n'''
            '''        parameter_values_path: Location of parameter values JSON.\n'''
            '''        pipeline_spec_path: Location of the pipeline spec JSON.\n'''
            '''        display_name: Name to call the pipeline.\n'''
            '''        enable_caching: Should caching be enabled (Boolean)\n'''
            '''    """\n'''
            '''    with open(parameter_values_path, 'r') as file:\n'''
            '''        try:\n'''
            '''            pipeline_params = json.load(file)\n'''
            '''        except ValueError as exc:\n'''
            '''            print(exc)\n'''
            '''    logging.debug('Pipeline Parms Configured:')\n'''
            '''    logging.debug(pipeline_params)\n'''
            '\n'
            '''    aiplatform.init(project=project_id)\n'''
            '''    job = aiplatform.PipelineJob(\n'''
            '''        display_name = display_name,\n'''
            '''        template_path = pipeline_spec_path,\n'''
            '''        pipeline_root = pipeline_root,\n'''
            '''        parameter_values = pipeline_params,\n'''
            '''        enable_caching = enable_caching)\n'''
            '''    logging.debug('AI Platform job built. Submitting...')\n'''
            '''    job.submit(service_account=pipeline_runner_sa)\n'''
            '''    logging.debug('Job sent!')\n'''
            '\n'
            '''if __name__ == '__main__':\n'''
            '''    parser = argparse.ArgumentParser()\n'''
            '''    parser.add_argument('--config', type=str,\n'''
            '''                        help='The config file for setting default values.')\n'''
            '''    args = parser.parse_args()\n'''
            '\n'
            '''    with open(args.config, 'r', encoding='utf-8') as config_file:\n'''
            '''        config = yaml.load(config_file, Loader=yaml.FullLoader)\n'''
            '\n'
            '''    run_pipeline(project_id=config['gcp']['project_id'],\n'''
            '''                 pipeline_root=config['pipelines']['pipeline_storage_path'],\n'''
            '''                 pipeline_runner_sa=config['gcp']['pipeline_runner_service_account'],\n'''
            '''                 parameter_values_path=config['pipelines']['parameter_values_path'],\n'''
            '''                 pipeline_spec_path=config['pipelines']['pipeline_job_spec_path']) \n''')

if __name__ == "__main__":
    print('Test')