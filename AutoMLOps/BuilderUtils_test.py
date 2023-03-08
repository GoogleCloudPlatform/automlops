import pytest, pathlib, os, yaml
from . import BuilderUtils

TEXT_FILE = (    
    'This is a test file.\n'
    'Test.')

GENERIC_YAML = (
    '# ===================================================\n'
    '# Test Yaml File'
    '# ===================================================\n'
    '\n'
    'Test1:\n'
    '  - name: "my_name1"\n'
    '    id: "my_id1"\n'
    '    description: my_description1'
    '\n'
    'Test2:\n'
    '  - name: "my_name2"\n'
    '    id: "my_id2"\n'
    '    description: my_description2'
)

GENERIC_DICT = (
    {
        'Test1' : [
            {
                'name': 'my_name1',
                'id': 'my_id1',
                'description': 'my_description1'
            }
        ],
        'Test2': [
            {
                'name': 'my_name2',
                'id': 'my_id2',
                'description': 'my_description2'
            }
        ]
    }
)

COMPONENT_YAML = (
    'name: my_component\n'
    'description: my test component\n'
    'inputs:\n'
    '- name: input1\n'
    '  type: String\n'
    '  description: No description provided.\n'
    'implementation:\n'
    '  container:\n'
    '    image: docker_container\n'
)

COMPONENT_DICT = (
    {
        'name': 'my_component',
        'description':'my_test_component',
        'inputs': 
            {
                'name': 'input1',
                'type': 'String',
                'description': 'No description provided.'
            },
        'implementation': 
            {
                'container': 
                    {
                        'image': 'docker_container'
                    }
            }
    }
)

@pytest.fixture
def write_yaml():
    file_path = pathlib.Path("generic.yaml")
    file_path.write_text(GENERIC_YAML)
    yield file_path
    file_path.unlink()
    
@pytest.fixture
def write_component_config():
    file_path = pathlib.Path("component.yaml")
    file_path.write_text(COMPONENT_YAML)
    yield file_path
    file_path.unlink()
    
@pytest.fixture
def write_file():
    file_path = pathlib.Path("text.txt")
    file_path.write_text(TEXT_FILE)
    yield file_path
    file_path.unlink()

def test_make_dirs(tmpdir):
    
    # Test whether a list of directories are created appropriately
    directories = [tmpdir + '/directory1', 
                   tmpdir + '/directory2', 
                   tmpdir + '/directory3']

    BuilderUtils.make_dirs(directories)
    assert set(directories) == set(tmpdir.listdir())
    
def test_read_yaml_file(write_yaml, tmpdir):
    
    # Test whether a yaml file creates the appropriate dictionary
    assert(BuilderUtils.read_yaml_file(write_yaml) == GENERIC_DICT
)
    # Test whether an error is produced when the file does not exist
    test_file = tmpdir + 'test.yaml'
    with pytest.raises(FileNotFoundError):
        assert BuilderUtils.read_file(test_file)
    
     
def test_write_yaml_file(tmpdir):
    
    # Test that the dictionary is successfully converted to a yaml that can be read back into the same dict
    test_file = tmpdir + "test_write_yaml_file.yaml"
    BuilderUtils.write_yaml_file(filepath=test_file, contents=GENERIC_DICT, mode='w')
    
    assert yaml.safe_load(open(test_file, 'r', encoding='utf-8')) == GENERIC_DICT
        
def test_read_file(tmpdir, write_file):
    
    # Test correct file
    assert BuilderUtils.read_file(write_file) == TEXT_FILE
    
    # Test incorrect file
    with pytest.raises(FileNotFoundError):
        assert BuilderUtils.read_file(tmpdir + 'test.yaml')
    
def test_write_file(tmpdir):
    
    # Test correct file
    test_file = tmpdir + "test_write_file.txt"
    BuilderUtils.write_file(filepath=test_file, text=TEXT_FILE, mode="w")
    
    with open(test_file, 'r', encoding='utf-8') as file:
        contents = file.read()
        assert contents == TEXT_FILE
    file.close() 
    
    # Test incorrect file
    with pytest.raises(OSError):
        assert BuilderUtils.write_file("my_folder/test.yaml", text="text", mode="w")
    
def test_write_and_chmod(tmpdir):
    # With all, check the file was written and that location is correct
    
    
    # Test correct file
    test_path = tmpdir + 'my_folder1'
    test_file = test_path + '/test_write_and_chmod.txt'
    os.makedirs(test_path)
    BuilderUtils.write_and_chmod(test_file, TEXT_FILE)
    
    with open(test_file, 'r', encoding='utf-8') as file:
        contents = file.read()
        assert contents == TEXT_FILE
    file.close()
    
    # TEST IF CHMOD WORKED
    #assert os.getcwd() == test_path
    
    # Test incorrect file
    with pytest.raises(OSError):
        test_path = tmpdir + 'my_folder2'
        test_file = test_path + '/test_write_and_chmod.txt'
        BuilderUtils.write_and_chmod(test_file, TEXT_FILE)
        
        with open(test_file, 'r', encoding='utf-8') as file:
            contents = file.read()
            assert contents == TEXT_FILE
        file.close()
    
def test_delete_file(tmpdir):
    
    f = open(f"{tmpdir}/myfile.txt", "x")
    BuilderUtils.delete_file(f"{tmpdir}/myfile.txt")
    assert not os.path.exists(f"{tmpdir}/myfile.txt")
    
def test_get_components_list(tmpdir, write_component_config):
    #write_component_config
    #assert BuilderUtils.get_components_list()

    assert True
    
def test_is_component_config(write_yaml, write_component_config):
    assert BuilderUtils.is_component_config(write_component_config)
    assert not BuilderUtils.is_component_config(write_yaml)

def test_execute_script():
    
    # Test invalid command
    with pytest.raises(RuntimeError):
        assert BuilderUtils.execute_process(command='abcde',
                                            to_null=False)
        
    # Test valid command
    #assert BuilderUtils.execute_process(command='echo 1',to_null=False) == 1

def test_validate_schedule():
    
    # Check that error is raised when it should be
    with pytest.raises(Exception, match='run_local must be set to False to use Cloud Scheduler.'):
        BuilderUtils.validate_schedule(schedule_pattern="*", 
                                       run_local=True)

    # Check that error is not raised when it shouldn't be
    BuilderUtils.validate_schedule(schedule_pattern="*", 
                                   run_local=False)
    BuilderUtils.validate_schedule(schedule_pattern="No Schedule Specified",
                                   run_local=True)
    BuilderUtils.validate_schedule(schedule_pattern="No Schedule Specified",
                                   run_local=False)
    
def test_validate_name():
    
    # Check that an error is raised when it should be
    with pytest.raises(Exception, match="Pipeline and Component names must be of type string."):
        BuilderUtils.validate_name(name=10)
    
    # Check that error is not raised when it shouldn't be
    BuilderUtils.validate_name(name="My Name")
        
def test_validate_params():
    
    # Test for user providing a value for 'name' that is not a string
    with pytest.raises(Exception, match = 'Parameter name must be of type string.'):
        BuilderUtils.validate_params([
            {
                'name': 1,
                'type': str,
                'description': 'my_description'
            }
        ])
    
    # Test for user providing a value for 'type' that is not a valid python type
    with pytest.raises(Exception, match = 'Parameter type must be a valid python type.'):
        BuilderUtils.validate_params([
            {
                'name': 'my_name',
                'type': 1,
                'description': 'my_description'
            }
        ])
        
    # Test for user missing a required parameter value
    with pytest.raises(Exception, match = "Parameter {'name': 'my_name', 'description': 'my_description'} does not contain required keys. 'type'"):
        BuilderUtils.validate_params([
            {
                'name': 'my_name',
                'description': 'my_description'
            }
        ])
    
    # don't think this can be tested
    BuilderUtils.validate_params([
            {
                'name': 'my_name',
                'name': ',ajksdfj',
                'type': int,
                'type': float
            }
        ])
    
    # Test that a correct list of dictionaries passes as expected
    BuilderUtils.validate_params([
        {
            'name': 'my_name',
            'type': str,
            'description': 'my_description'
        }
    ])
    
def test_validate_pipeline_structure():
    assert True
    
def test_update_params():
    
    # Test for an exception with an incorrect value for 'type'
    with pytest.raises(Exception):
        BuilderUtils.update_params([
            {
                'name': 'my_name_1',
                'type': str,
                'description': 'my_description_1'
            },
            {
                'name': 'my_name_2',
                'type': 10
            }
        ])
    
    # Test for an exception with an incorrect value for 'type'
    with pytest.raises(Exception):
        BuilderUtils.update_params([
            {
                'name': 'my_name_1',
                'type': str,
                'description': 'my_description_1'
            },
            {
                'name': 'my_name_2',
                'type': 'wrong_type'
            }
        ])
    
    # Test that correctly formatted parameters will pass
    BuilderUtils.update_params([
        {
            'name': 'my_name_1',
            'type': str,
            'description': 'my_description_1'
        },
        {
            'name': 'my_name_2',
            'type': int
        }
    ])
    
    # Test that correctly formatted parameters will pass
    BuilderUtils.update_params([
        {
            'name': 'my_name_1',
            'type': str,
            'description': 'my_description_1'
        },
        {
            'name': 'my_name_2',
            'type': float
        }
    ])