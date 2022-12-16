import errno
import re
import os
import yaml

class ComponentBuilder:
    def __init__(self):
        self.component_def = ""
        self.component_dir = ""
        self.image = ""
        self.installs = ""
        self.task_contents = ""
    
    def formalize(self, component_path, top_lvl_name, defaults_file):
        self.component_def = self.read_yaml_file(component_path)
        self.component_name = self.get_component_name(component_path)
        self.component_dir = top_lvl_name + 'components/' + self.component_def['implementation']['container']['args'][-1]
        self.image = self.component_def['implementation']['container']['image']
        self.installs = self.component_def['implementation']['container']['command'][2]
        self.task_contents = self.component_def['implementation']['container']['command'][-1]
        self.setup_dir()
        self.create_requirements()
        self.create_dockerfile()
        self.create_task()
        self.update_def(component_path, defaults_file)

    def read_yaml_file(self, file_path):
        with open(file_path, 'r') as file:
            try:
                file_dict = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
        file.close()
        return file_dict
    
    def get_component_name(self, file_path):
        return os.path.basename(file_path).split('.')[0]
            
    def setup_dir(self):
        try:
            os.makedirs(self.component_dir)
            os.makedirs(os.path.join(self.component_dir, 'trainer'))
        except OSError as e:
            if errno.EEXIST != e.errno:
                raise
        # maybe move yaml into component dir?
    
    def create_requirements(self):
        formatted_installs = re.findall('\'([^\']*)\'', self.installs)
        filename = os.path.join(self.component_dir, "requirements.txt")
        with open(filename, "w") as file:
            for element in formatted_installs:
                file.write(element+'\n')
        file.close()

    def create_dockerfile(self):
        structure = f"""FROM {self.image}
RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN python -m pip install -r \
    requirements.txt --quiet --no-cache-dir \
    && rm -f requirements.txt
WORKDIR /
COPY trainer /trainer
ENTRYPOINT ["python", "-m", "trainer.task"]"""
        with open(os.path.join(self.component_dir, "Dockerfile"), "w") as file:
            file.write(structure)
        file.close()

    def create_task(self):
        wrapper = ['''import argparse
import json
from kfp.v2.components import executor''',
'''def main():
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
    main()''']
        with open(os.path.join(self.component_dir, 'trainer/task.py'), "w") as file:
            file.write(wrapper[0])
            file.write(self.task_contents)
            file.write(wrapper[1])
        file.close()

    def update_def(self, file_path, defaults_file):
        with open(defaults_file, 'r') as file:
            try:
                defs = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
        self.component_def['implementation']['container']['image'] = f"{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/{self.component_name}:latest"
        self.component_def['implementation']['container']['command'] = ['python3', '-u', '-m', 'trainer.task']
        filename = os.path.join(self.component_dir, "component.yaml")
        with open(filename, 'w') as file:
            yaml.dump(self.component_def, file, sort_keys=False)
        os.remove(file_path) # remove old file