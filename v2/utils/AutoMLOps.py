import errno
import os
import yaml

# need to update this sys pathing
from . import ComponentBuilder
from . import PipelineBuilder
from . import JupyterUtilsMagic

TOP_LVL_NAME = 'AutoMLOps/'
DEFAULTS_FILE = TOP_LVL_NAME + 'configs/defaults.yaml'
PIPELINE_SPEC_SH_FILE = TOP_LVL_NAME + 'scripts/build_pipeline_spec.sh'
BUILD_COMPONENTS_SH_FILE = TOP_LVL_NAME + 'scripts/build_components.sh'
RUN_PIPELINE_SH_FILE = TOP_LVL_NAME + 'scripts/run_pipeline.sh'
RUN_ALL_SH_FILE = TOP_LVL_NAME + 'scripts/run_all.sh'
RESOURCES_SH_FILE = TOP_LVL_NAME + 'scripts/create_resources.sh'
CLOUDBUILD_FILE = TOP_LVL_NAME + 'cloudbuild.yaml'
PIPELINE_FILE = TOP_LVL_NAME + 'pipelines/pipeline.py'
IMPORTS_FILE = '.imports.py'
DEFAULT_IMAGE = 'python:3.9'
COMPONENT_BASE = TOP_LVL_NAME + 'components/component_base'
COMPONENT_BASE_SRC = TOP_LVL_NAME + 'components/component_base/src'
DIRS = [
    TOP_LVL_NAME,
    TOP_LVL_NAME + 'components',
    TOP_LVL_NAME + 'components/component_base',
    TOP_LVL_NAME + 'components/component_base/src',
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
    write_cloudbuild_yaml()
    cb = ComponentBuilder.ComponentBuilder()
    pb = PipelineBuilder.PipelineBuilder()
    for path in components_path_list:
        cb.formalize(path, TOP_LVL_NAME, DEFAULTS_FILE)
    pb.formalize(pipeline_params, parameter_values_path, TOP_LVL_NAME)
    autoflake_srcfiles() # Remove unused imports from python files
    create_requirements()
    create_dockerfile()

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
# Builds the pipeline specs
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
# Submits the PipelineJob to Vertex AI
# This script should run from the main directory
# Change directory in case this isn't the script root.

CONFIG_FILE=configs/defaults.yaml

python3 -m pipelines.pipeline_runner --config $CONFIG_FILE
"""
    run_all= """#! /bin/bash
# Builds components, pipeline specs, and submits the PipelineJob.
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

def write_cloudbuild_yaml():
    with open(DEFAULTS_FILE, 'r') as file:
        try:
            defs = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    cloud_build_yaml = f"""steps:
# ==============================================================================
# BUILD CUSTOM COMPONENT IMAGES
# ==============================================================================

  # build the component-base image
  - name: "gcr.io/cloud-builders/docker"
    args: [ "build", "-t", "{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/component_base:latest", "." ]
    dir: '{TOP_LVL_NAME}components/component_base'
    id: 'Build image: component base'

images:
  # custom component images
  - "{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/component_base:latest"
 """
    with open(CLOUDBUILD_FILE, 'w+') as file:
        file.write(cloud_build_yaml)
    file.close()

def create_requirements():
    # db_types, pyarrow, gcsfs, fsspec are sometimes missing in setup.py files
    google_cloud_reqs = """db_dtypes
pyarrow
gcsfs
fsspec
google-cloud-aiplatform
google-cloud-appengine-logging
google-cloud-audit-log
google-cloud-bigquery
google-cloud-bigquery-storage
google-cloud-bigtable
google-cloud-core
google-cloud-dataproc
google-cloud-datastore
google-cloud-dlp
google-cloud-firestore
google-cloud-kms
google-cloud-language
google-cloud-logging
google-cloud-monitoring
google-cloud-notebooks
google-cloud-pipeline-components
google-cloud-pubsub
google-cloud-pubsublite
google-cloud-recommendations-ai
google-cloud-resource-manager
google-cloud-scheduler
google-cloud-spanner
google-cloud-speech
google-cloud-storage
google-cloud-tasks
google-cloud-translate
google-cloud-videointelligence
google-cloud-vision"""
    #os.system(f'python3 -m pip list --format=freeze --exclude pip > {COMPONENT_BASE}/requirements.txt')
    os.system(f'python3 -m pipreqs.pipreqs {COMPONENT_BASE} --mode no-pin --force &>/dev/null')
    with open(f'{COMPONENT_BASE}/requirements.txt', 'a') as file:
       file.write(google_cloud_reqs)
    file.close()

def create_dockerfile():
    structure = f"""FROM {DEFAULT_IMAGE}
RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN python -m pip install -r \
    requirements.txt --quiet --no-cache-dir \
    && rm -f requirements.txt
COPY ./src /pipelines/component/src
ENTRYPOINT ["/bin/bash"]"""
    with open(os.path.join(COMPONENT_BASE, "Dockerfile"), "w") as file:
        file.write(structure)
    file.close()

def autoflake_srcfiles():
    os.system(f'python3 -m autoflake --in-place --remove-all-unused-imports {COMPONENT_BASE_SRC}/*.py')

def get_components_from_yamls(directory: str):
    components_list = []
    elements = os.listdir(directory)
    for file in list(filter(lambda y: ('.yaml' or 'yml') in y, elements)):
        if is_component_yaml_file(os.path.join(directory, file)):
            components_list.append(file)
    return components_list

def is_component_yaml_file(file_path: str):
    required_keys = ['name','inputs','implementation']
    with open(file_path, 'r') as file:
        try:
            file_dict = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    file.close()
    return all(key in file_dict.keys() for key in required_keys)

#### These functions are not included as part of generate workflow - they are called directly ####

def makeComponent(name: str,
                  params: list,
                  description: str = None):
    if type(name) is not str:
        print("Component name must be a string")

    validate_params(params)
    func_def = get_func_definition(name, params, description)
    update_params(params)

    with open(".cell.py", 'r') as f:
        code = f.read()
        code = filter_and_format_cell(code)
    f.close()
    os.remove(".cell.py")

    # make yaml
    component_dict = {}
    component_dict['name'] = name
    if description:
        component_dict['description'] = description
    component_dict['inputs'] = params

    component_dict['implementation'] = {}
    component_dict['implementation']['container'] = {}
    component_dict['implementation']['container']['image'] = 'TBD'
    component_dict['implementation']['container']['command'] = func_def + code
    component_dict['implementation']['container']['args'] = ['--executor_input', {'executorInput': None}, '--function_to_execute', name]

    with open(f"{name}.yaml", 'w') as file:
        yaml.safe_dump(component_dict, file, sort_keys=False)

def validate_params(params: list):
    s = set()
    for param in params:
        try:
            name = param['name']
            if type(name) is not str:
                print("Parameter name must be a string")
            param_type = param['type']
            if not isinstance(param_type, type):
                print("type is not a valid python type")
        except KeyError:
            print("Does not contain required keys")
        if param['name'] in s:
            print(f"Duplicate parameter {param['name']}")
        else:
            s.add(param['name'])

def validate_pipeline_structure(pipeline: list):
    # re-work this
    components_list = os.listdir('./')
    components_list = [comp.replace('.yaml', '') for comp in components_list if '.yaml' in comp]

    for component in pipeline:
        try:
            component_name = component['component_name']
            if component_name not in components_list:
                print(f"Component {component_name} not found! Not matching yaml definition in local directory")
            param_mapping = component['param_mapping']
        except KeyError:
            print("Does not contain required keys")  
        for param_tuple in param_mapping:
            if type(param_tuple) is not tuple:
                print(f"Mapping contains a non-tuple element {param_tuple}")
            elif len(param_tuple) != 2:
                print(f"Mapping must contain only 2 elements, tuple {param_tuple} is invalid.")
            else:
                for item in param_tuple:
                    if type(item) is not str:
                        print(f"Mapping must be str-str, tuple {param_tuple} is invalid.")

def update_params(params: list):
    # Only supporting primitive types at this time
    python_kfp_types_mapper = {
        int: 'Integer',
        str: 'String',
        float: 'Float',
        bool: 'Bool',
        list: 'List',
        dict: 'Dict'
    }
    for param in params:
        try:
            param['type'] = python_kfp_types_mapper[param['type']]
        except KeyError:
            print("Unsupported python type - we only support primitive types at this time.")

def get_func_definition(name: str,
                        params: list,
                        description: str):
    triple_quotes = "\"\"\""
    newline = '\n'
    return f"""
def {name}(
{newline.join(f"    {param['name']}: {param['type'].__name__}," for param in params)}
):
    {triple_quotes}{description}

    Args:
{newline.join(f"        {param['name']}: {param['description']}," for param in params)}
    {triple_quotes}"""

def filter_and_format_cell(code: str):
    """Remove unwanted parts; indent"""
    code = code.replace(code[code.find("AutoMLOps.makeComponent("):code.find(")")+1], "")
    indented_code = ""
    for line in code.splitlines():
        indented_code += '    ' + line + '\n'
    return indented_code


def makePipeline(name: str,
                 params: list,
                 pipeline: list,
                 description: str = None):
    if type(name) is not str:
        print("Pipeline name must be a string")

    validate_params(params)
    validate_pipeline_structure(pipeline)
    pipeline_def = get_pipeline_definition(name, params, pipeline, description)
    with open(f"pipeline.py", 'w') as file:
        file.write(pipeline_def)
    file.close()

def get_pipeline_definition(name: str,
                            params: list,
                            pipeline: list,
                            description: str):
    triple_quotes = "\"\"\""
    newline = '\n'
    queue = ['']
    for idx, component in enumerate(pipeline):
        if idx != len(pipeline)-1:
            queue.append(f".after({component['component_name']}_task)")
    return f"""
@dsl.pipeline(
    name='{name}',
    description='{description}')
def pipeline(
{newline.join(f"    {param['name']}: {param['type'].__name__}," for param in params)}
):
    {triple_quotes}{description}

    Args:
{newline.join(f"        {param['name']}: {param['description']}," for param in params)}
    {triple_quotes}
{"".join(f'''
    {component['component_name']}_task = {component['component_name']}(
    {f'{newline}    '.join(f"   {param[0]}={param[1]}," for param in component['param_mapping'])}
    ){queue.pop(0)}
''' for component in pipeline
)}
"""