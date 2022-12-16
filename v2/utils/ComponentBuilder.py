import errno
import os
import yaml

IMPORTS_FILE = '.imports.py'

class ComponentBuilder:
    def __init__(self):
        self.component_def = ""
        self.component_dir = ""
        self.src_dir = ""
        self.component_py =""
    
    def formalize(self, component_path, top_lvl_name, defaults_file):
        self.component_def = self.read_yaml_file(component_path)
        self.src_dir = top_lvl_name + 'components/component_base/src'
        self.component_dir = top_lvl_name + 'components/' + self.component_def['name']
        self.component_py = self.component_def['name']+'.py'
        self.create_component_dir()
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
            
    def create_component_dir(self):
        try:
            os.makedirs(self.component_dir)
        except OSError as e:
            if errno.EEXIST != e.errno:
                raise

    def create_task(self):
        # check if file exists
        try:
            with open(IMPORTS_FILE, 'r') as file:
                imports = file.read()
            file.close()
        except FileNotFoundError:
            print("Imports file not found. Rerun imports cell")

        wrapper = ['''import argparse
import json
from kfp.v2.components import executor
''',
'''
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
    main()''']
        with open(os.path.join(self.src_dir, self.component_py), "w+") as file:
            file.write(wrapper[0])
            file.write(imports)
            file.write(self.component_def['implementation']['container']['command'])
            file.write(wrapper[1])
        file.close()

    def update_def(self, file_path, defaults_file):
        with open(defaults_file, 'r') as file:
            try:
                defs = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
        self.component_def['implementation']['container']['image'] = f"{defs['gcp']['af_registry_location']}-docker.pkg.dev/{defs['gcp']['project_id']}/{defs['gcp']['af_registry_name']}/components/component_base:latest"
        self.component_def['implementation']['container']['command'] = ['python3', f'/pipelines/component/src/{self.component_py}']
        filename = os.path.join(self.component_dir, "component.yaml")
        with open(filename, 'w') as file:
            yaml.dump(self.component_def, file, sort_keys=False)
        os.remove(file_path) # remove old file