# Copyright 2023 Google LLC. All Rights Reserved.
#
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

"""Builds component files."""

from AutoMLOps import BuilderUtils

# pylint: disable=line-too-long
def formalize(component_path: str,
              top_lvl_name: str,
              defaults_file: str,
              use_kfp_spec: bool):
    """Constructs and writes component.yaml and {component_name}.py files.
        component.yaml: Contains the Kubeflow custom component definition.
        {component_name}.py: Contains the python code from the Jupyter cell.

    Args:
        component_path: Path to the temporary component yaml. This file
            is used to create the permanent component.yaml, and deleted
            after calling AutoMLOps.generate().
        top_lvl_name: Top directory name.
        defaults_file: Path to the default config variables yaml.
        use_kfp_spec: Flag that determines the format of the component yamls.
    """
    component_spec = BuilderUtils.read_yaml_file(component_path)
    if use_kfp_spec:
        component_spec['name'] = component_spec['name'].replace(' ', '_').lower()
    component_dir = top_lvl_name + 'components/' + component_spec['name']
    task_filepath = (top_lvl_name + 'components/component_base/src/' +
                     component_spec['name'] + '.py')
    BuilderUtils.make_dirs([component_dir])
    create_task(component_spec, task_filepath, use_kfp_spec)
    create_component(component_spec, component_dir, defaults_file)

def create_task(component_spec: dict, task_filepath: str, use_kfp_spec: bool):
    """Writes cell python code to a file with required imports.

    Args:
        component_spec: Component definition dictionary.
            Contains cell code which is temporarily stored in
            component_spec['implementation']['container']['command']
        task_filepath: Path to the file to be written.
        use_kfp_spec: Flag that determines the format of the component yamls.
    Raises:
        Exception: If the imports tmpfile does not exist.
    """
    if use_kfp_spec:
        custom_imports = ''
        custom_code = component_spec['implementation']['container']['command'][-1]
    else:
        custom_imports = BuilderUtils.read_file(BuilderUtils.IMPORTS_TMPFILE)
        custom_code = component_spec['implementation']['container']['command']
    default_imports = (BuilderUtils.LICENSE +
        'import argparse\n'
        'import json\n'
        'from kfp.v2.components import executor\n')
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
    f_contents = default_imports + custom_imports + custom_code + main_func
    BuilderUtils.write_file(task_filepath, f_contents, 'w+')

def create_component(component_spec: dict,
                     component_dir: str,
                     defaults_file: str):
    """Updates the component_spec to include the correct image
       and startup command, then writes the component.yaml.
       Requires a defaults.yaml config to pull config vars from.

    Args:
        component_spec: Component definition dictionary.
        component_dir: Path of the component directory.
        defaults_file: Path to the default config variables yaml.
    Raises:
        Exception: If an error is encountered writing the file.
    """
    defaults = BuilderUtils.read_yaml_file(defaults_file)
    component_spec['implementation']['container']['image'] = (
        f'''{defaults['gcp']['af_registry_location']}-docker.pkg.dev/'''
        f'''{defaults['gcp']['project_id']}/'''
        f'''{defaults['gcp']['af_registry_name']}/'''
        f'''components/component_base:latest''')
    component_spec['implementation']['container']['command'] = [
        'python3',
        f'''/pipelines/component/src/{component_spec['name']+'.py'}''']
    filename = component_dir + '/component.yaml'
    BuilderUtils.write_file(filename, BuilderUtils.LICENSE, 'w')
    BuilderUtils.write_yaml_file(filename, component_spec, 'a')

def create_component_scaffold(name: str,
                              params: list,
                              description: str):
    """Creates a tmp component scaffold which will be used by
       the formalize function. Code is temporarily stored in
       component_spec['implementation']['container']['command'].

    Args:
        name: Component name.
        params: Component parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        description: Optional description of the component.
    """
    BuilderUtils.validate_name(name)
    BuilderUtils.validate_params(params)
    func_def = get_func_definition(name, params, description)
    params = BuilderUtils.update_params(params)
    code = BuilderUtils.read_file(BuilderUtils.CELL_TMPFILE)
    code = filter_and_indent_cell(code)
    BuilderUtils.delete_file(BuilderUtils.CELL_TMPFILE)
    # make yaml
    component_spec = {}
    component_spec['name'] = name
    if description:
        component_spec['description'] = description
    component_spec['inputs'] = params
    component_spec['implementation'] = {}
    component_spec['implementation']['container'] = {}
    component_spec['implementation']['container']['image'] = 'TBD'
    component_spec['implementation']['container']['command'] = func_def + code
    component_spec['implementation']['container']['args'] = ['--executor_input',
        {'executorInput': None}, '--function_to_execute', name]
    filename = BuilderUtils.TMPFILES_DIR + f'/{name}.yaml'
    BuilderUtils.write_yaml_file(filename, component_spec, 'w')

def get_func_definition(name: str,
                        params: list,
                        description: str):
    """Generates a python function definition to be used in
       the {component_name}.py file (this file will contain
       Jupyter cell code).

    Args:
        name: Component name.
        params: Component parameters. A list of dictionaries,
            each param is a dict containing keys:
                'name': required, str param name.
                'type': required, python primitive type.
                'description': optional, str param desc.
        description: Optional description of the component.
    """
    newline = '\n'
    return (
        f'\n'
        f'def {name}(\n'
        f'''{newline.join(f"    {param['name']}: {param['type'].__name__}," for param in params)}\n'''
        f'):\n'
        f'    """{description}\n'
        f'\n'
        f'    Args:\n'
        f'''{newline.join(f"        {param['name']}: {param['description']}," for param in params)}\n'''
        f'    """'
    )

def filter_and_indent_cell(code: str) -> str:
    """Remove unwanted makeComponent function call
       and indent cell code.

    Args:
        code: String contains the contents of the
            Jupyter cell.
    Return:
        str: Indented cell code with removed func call.
    """
    code = code.replace(code[code.find('AutoMLOps.makeComponent('):code.find(')')+1], '')
    indented_code = ''
    for line in code.splitlines():
        indented_code += '    ' + line + '\n'
    return indented_code
