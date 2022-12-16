import errno
import os
import yaml

# need to update this sys pathing
from . import ComponentBuilder
from . import PipelineBuilder

TOP_LVL_NAME = 'MLOpsBox/'
DEFAULTS_FILE = TOP_LVL_NAME + 'configs/defaults.yaml'
PIPELINE_SPEC_SH_FILE = TOP_LVL_NAME + 'scripts/build_pipeline_spec.sh'
BUILD_COMPONENTS_SH_FILE = TOP_LVL_NAME + 'scripts/build_components.sh'
RUN_PIPELINE_SH_FILE = TOP_LVL_NAME + 'scripts/run_pipeline.sh'
RUN_ALL_SH_FILE = TOP_LVL_NAME + 'scripts/run_all.sh'
RESOURCES_SH_FILE = TOP_LVL_NAME + 'scripts/create_resources.sh'
CLOUDBUILD_FILE = TOP_LVL_NAME + 'cloudbuild.yaml'
PIPELINE_FILE = TOP_LVL_NAME + 'pipelines/pipeline.py'
DIRS = [
    TOP_LVL_NAME,
    TOP_LVL_NAME + 'components',
    TOP_LVL_NAME + 'configs',
    TOP_LVL_NAME + 'images',
    TOP_LVL_NAME + 'pipelines',
    TOP_LVL_NAME + 'pipelines/runtime_parameters',
    TOP_LVL_NAME + 'scripts',
    TOP_LVL_NAME + 'scripts/pipeline_spec'
]

def go(project_id: str,
       pipeline_params: dict,
       af_registry_location: str = "us-central1",
       af_registry_name: str = "vertex-mlops-af",
       gs_bucket_location: str = "us-central1",
       gs_bucket_name: str = "",
       parameter_values_path: str = "pipelines/runtime_parameters/pipeline_parameter_values.json",
       pipeline_job_spec_path: str = "scripts/pipeline_spec/pipeline_job.json",
       yamls_directory: str = "./"):
    # Make stuff and run it
    generate(project_id, pipeline_params, af_registry_location,
             af_registry_name, gs_bucket_location, gs_bucket_name, 
             parameter_values_path, pipeline_job_spec_path, yamls_directory)
    run()

def generate(project_id: str,
       pipeline_params: dict,
       af_registry_location: str = "us-central1",
       af_registry_name: str = "vertex-mlops-af",
       gs_bucket_location: str = "us-central1",
       gs_bucket_name: str = "",
       parameter_values_path: str = "pipelines/runtime_parameters/pipeline_parameter_values.json",
       pipeline_job_spec_path: str = "scripts/pipeline_spec/pipeline_job.json",
       yamls_directory: str = "./"):
    # Make stuff
    make_dirs()
    try:
        os.rename('pipeline.py', PIPELINE_FILE)
    except OSError as e:
        if errno.EEXIST != e.errno:
            raise
    components_path_list = get_components_from_yamls(yamls_directory)
    default_bucket_name = f"{project_id}-bucket" if gs_bucket_name == "" else gs_bucket_name
    write_default_config(project_id, af_registry_location, af_registry_name,
                         gs_bucket_location, default_bucket_name, parameter_values_path,
                         pipeline_job_spec_path)
    handle_scripts()
    create_resources(project_id, af_registry_location,
                     af_registry_name, gs_bucket_location, 
                     default_bucket_name)
    write_cloudbuild_yaml([get_component_name(path) for path in components_path_list])
    cb = ComponentBuilder.ComponentBuilder()
    pb = PipelineBuilder.PipelineBuilder()
    for path in components_path_list:
        cb.formalize(path, TOP_LVL_NAME, DEFAULTS_FILE)
    pb.formalize(pipeline_params, parameter_values_path, TOP_LVL_NAME)

def run():
    # run
    os.chdir(TOP_LVL_NAME)
    os.system("./scripts/run_all.sh")
    os.chdir("../")

def make_dirs():
    for dir in DIRS:
        try:
            os.makedirs(dir)
        except OSError as e:
            if errno.EEXIST != e.errno:
                raise

def get_component_name(file_path: str):
    return os.path.basename(file_path).split('.')[0]

def write_default_config(project_id: str,
                         af_registry_location: str,
                         af_registry_name: str,
                         gs_bucket_location: str,
                         gs_bucket_name: str,
                         parameter_values_path: str,
                         pipeline_job_spec_path: str):
    defaults = f"""gcp:
  project_id: {project_id}
  af_registry_location: {af_registry_location}
  af_registry_name: {af_registry_name}

pipelines:
  pipeline_region: {gs_bucket_location}
  parameter_values_path: {parameter_values_path}
  pipeline_storage_path: gs://{gs_bucket_name}/pipeline_root
  pipeline_component_directory: components
  pipeline_job_spec_path: {pipeline_job_spec_path}
"""
    with open(DEFAULTS_FILE, 'w+') as file:
        file.write(defaults)
    file.close()

def write_with_privs(filename: str, text: str):
    with open(filename, 'w+') as file:
        file.write(text)
    file.close()
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | 0o111)

def handle_scripts():
    build_pipeline_spec = """#! /bin/bash
# Build the training pipeline specs
# This script should run from the main directory
# Change directory in case this isn't the script root.

CONFIG_FILE=configs/defaults.yaml

python3 -m pipelines.pipeline --config $CONFIG_FILE
"""
    build_components = """#! /bin/bash
# Submits a Cloud Build job that builds and deploys the components
# This script should run from the main directory
# Change directory in case this isn't the script root.

gcloud builds submit .. --config cloudbuild.yaml --timeout=3600
"""
    run_pipeline = """#! /bin/bash
# Submit the PipelineJob to Vertex AI
# This script should run from the main directory
# Change directory in case this isn't the script root.

CONFIG_FILE=configs/defaults.yaml

python3 -m pipelines.pipeline_runner --config $CONFIG_FILE
"""
    run_all= """#! /bin/bash
# Build the training pipeline specs
# This script should run from the main directory
# Change directory in case this isn't the script root.

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN} BUILDING COMPONENTS ${NC}"
gcloud builds submit .. --config cloudbuild.yaml --timeout=3600

echo -e "${GREEN} BUILDING PIPELINE SPEC ${NC}"
./scripts/build_pipeline_spec.sh

echo -e "${GREEN} RUNNING PIPELINE JOB ${NC}"
./scripts/run_pipeline.sh
"""
    write_with_privs(PIPELINE_SPEC_SH_FILE, build_pipeline_spec)
    write_with_privs(BUILD_COMPONENTS_SH_FILE, build_components)
    write_with_privs(RUN_PIPELINE_SH_FILE, run_pipeline)
    write_with_privs(RUN_ALL_SH_FILE, run_all)

def create_resources(project_id: str,
                     af_registry_location: str,
                     af_registry_name: str,
                     gs_bucket_location: str,
                     gs_bucket_name: str):
    left_bracket = "{"
    right_bracket = "}"
    create_resources_script = f"""#! /bin/bash
# This script will create an artifact registry and gs bucket if they do not already exist.

AF_REGISTRY_NAME={af_registry_name}
AF_REGISTRY_LOCATION={af_registry_location}
PROJECT_ID={project_id}
BUCKET_NAME={gs_bucket_name}
BUCKET_LOCATION={gs_bucket_location}

if ! (gcloud artifacts repositories list --project="$PROJECT_ID" --location=$AF_REGISTRY_LOCATION | grep --fixed-strings "$AF_REGISTRY_NAME"); then

  gcloud artifacts repositories create "$AF_REGISTRY_NAME" \
    --repository-format=docker \
    --location=$AF_REGISTRY_LOCATION \
    --project="$PROJECT_ID" \
    --description="Artifact Registry ${left_bracket}AF_REGISTRY_NAME{right_bracket} in ${left_bracket}AF_REGISTRY_LOCATION{right_bracket}."
else

  echo "Artifact Registry: ${left_bracket}AF_REGISTRY_NAME{right_bracket} already exists in project $PROJECT_ID"

fi


if !(gsutil ls -b gs://$BUCKET_NAME | grep --fixed-strings "$BUCKET_NAME"); then

  gsutil mb -l ${left_bracket}BUCKET_LOCATION{right_bracket} gs://$BUCKET_NAME

else

  echo "GS Bucket: ${left_bracket}BUCKET_NAME{right_bracket} already exists in project $PROJECT_ID"

fi
"""
    write_with_privs(RESOURCES_SH_FILE, create_resources_script)
    os.system(f"./{RESOURCES_SH_FILE} &>/dev/null")

def write_cloudbuild_yaml(components_list: list):
    with open(DEFAULTS_FILE, 'r') as file:
        try:
            defs = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    newline = '\n'
    quotes = '"'
    cloud_build_yaml = f"""steps:
# ==============================================================================
# BUILD CUSTOM COMPONENT IMAGES
# ==============================================================================
{newline.join(f"  # build the {component} component image{newline}  - name: {quotes}gcr.io/cloud-builders/docker{quotes}{newline}    args: [ {quotes}build{quotes}, {quotes}-t{quotes}, {quotes}{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/{component}:latest{quotes}, {quotes}.{quotes} ]{newline}    dir: {quotes}{TOP_LVL_NAME}components/{component}{quotes}{newline}    id: {quotes}Build component: {component}{quotes}{newline}" for component in components_list)}

images:
  # custom component images
{newline.join(f"  - {quotes}{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/{component}:latest{quotes}" for component in components_list)}
"""
    with open(CLOUDBUILD_FILE, 'w+') as file:
        file.write(cloud_build_yaml)
    file.close()


def get_components_from_yamls(directory: str):
    components_list = []
    elements = os.listdir(directory)
    for file in list(filter(lambda y: ('.yaml' or 'yml') in y, elements)):
        if is_component_yaml_file(os.path.join(directory, file)):
            components_list.append(file)
    return components_list

def is_component_yaml_file(file_path: str):
    required_keys = ['name','inputs','outputs','implementation']
    with open(file_path, 'r') as file:
        try:
            file_dict = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    file.close()
    return all(key in file_dict.keys() for key in required_keys)