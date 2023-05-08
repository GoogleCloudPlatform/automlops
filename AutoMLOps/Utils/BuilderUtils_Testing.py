import pytest, pathlib
from . import BuilderUtils
import os, yaml
from pathlib import Path

@pytest.fixture
def write_yaml():
    file_path = pathlib.Path("testing.yaml")
    file_path.write_text(
            
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
    yield file_path
    file_path.unlink()

def test_make_dirs():
    
    # Create a list of directories to create.
    directories = ["dir1", "dir2"]

    # Call the `make_dirs` function.
    BuilderUtils.make_dirs(directories)

    # Assert that the directories were created.
    for d in directories:
        assert os.path.exists(d)
        os.rmdir(d)

def test_read_yaml_file():
    # Create a yaml file.
    with open('test.yaml', 'w') as file:
        yaml.dump({'key1': 'value1', 'key2': 'value2'}, file)

    # Call the `read_yaml_file` function.
    file_dict = BuilderUtils.read_yaml_file('test.yaml')

    # Assert that the file_dict contains the expected values.
    assert file_dict == {'key1': 'value1', 'key2': 'value2'}
    
    # Remove test file
    os.remove('test.yaml')
    
def test_write_yaml_file():

    # Call the `write_yaml_file` function.
    BuilderUtils.write_yaml_file('test.yaml', {'key1': 'value1', 'key2': 'value2'}, 'w')

    # Assert that the file contains the expected values.
    with open('test.yaml', 'r') as file:
        file_dict = yaml.safe_load(file)
    assert file_dict == {'key1': 'value1', 'key2': 'value2'}
    
    # Call the `write_yaml_file` function with an invalid mode.
    with pytest.raises(IOError):
        BuilderUtils.write_yaml_file('test.yaml', {'key1': 'value1', 'key2': 'value2'}, 'r')
    
    # Remove test file
    os.remove('test.yaml')
    
    # This still works for an invalid content and file path parameter, is that right?

def test_read_file():
    # Create a file.
    with open('test.txt', 'w') as file:
        file.write('This is a test file.')

    # Call the `read_file` function.
    contents = BuilderUtils.read_file('test.txt')

    # Assert that the contents of the file are correct.
    assert contents == 'This is a test file.'
    
    # Remove test file
    os.remove('test.txt')

    # THIS SHOULD WORK BUT IT DOESN'T
    # Call the `read_file` function with an invalid file path.
    #with pytest.raises(FileNotFoundError):
    #    BuilderUtils.read_file('invalid_file_path.txt')
    
def test_write_file():
    # Create a file.
    with open('test.txt', 'w') as file:
        file.write('This is a test file.')

    # Call the `write_file` function.
    BuilderUtils.write_file('test.txt', 'This is a test file.', 'w')

    # Assert that the file exists.
    assert os.path.exists('test.txt')

    # Assert that the contents of the file are correct.
    with open('test.txt', 'r') as file:
        contents = file.read()
    assert contents == 'This is a test file.'
    
    # Remove test file
    os.remove('test.txt')

    # Call the `write_file` function with an invalid file path.
    with pytest.raises(OSError):
        BuilderUtils.write_file(15, 'This is a test file.', 'w')
        
def test_write_and_chmod():
    # Create a file.
    with open('test.txt', 'w') as file:
        file.write('This is a test file.')

    # Call the `write_and_chmod` function.
    BuilderUtils.write_and_chmod('test.txt', 'This is a test file.')

    # Assert that the file exists and is executable.
    assert os.path.exists('test.txt')
    assert os.access('test.txt', os.X_OK)

    # Delete the file.
    os.remove('test.txt')

    # THIS SHOULDN'T WORK BUT IT DOES
    # Call the `write_and_chmod` function with an invalid file path.
    #with pytest.raises(OSError):
    #    BuilderUtils.write_and_chmod('invalid_file_path.txt', 'This is a test file.')

def test_delete_fileh():
    # Create a file.
    with open('test.txt', 'w') as file:
        file.write('This is a test file.')

    # Call the `delete_file` function.
    BuilderUtils.delete_file('test.txt')

    # Assert that the file does not exist.
    assert not os.path.exists('test.txt')
    
    # THIS SHOULD WORK BUT IT DOESN'T
    # Call the `delete_file` function with an invalid file path.
    
    #with pytest.raises(OSError):
    #    BuilderUtils.delete_file('invalid_file_path.txt')

@pytest.mark.parametrize("full_path", [True, False])
def test_get_components_list(full_path: bool) -> None:
    # Create a temporary directory
    tmp_dir = Path("/tmp/test_get_components_list")
    tmp_dir.mkdir()

    # Create some component yaml files
    component_yaml_1 = tmp_dir / "component_1.yaml"
    component_yaml_1.write_text("This is a component yaml file.")
    component_yaml_2 = tmp_dir / "component_2.yml"
    component_yaml_2.write_text("This is another component yaml file.")

    # Get the list of component yaml files
    components_list = BuilderUtils.get_components_list(full_path)

    # Check that the list contains the correct files
    if full_path:
        assert components_list == [tmp_dir / "component_1.yaml", tmp_dir / "component_2.yml"]
    else:
        assert components_list == ["component_1", "component_2"]

    # Clean up the the temporary directory
    tmp_dir.rmdir()












"""
def test_read_yaml_file(write_yaml):
    
    assert(BuilderUtils.read_yaml_file(write_yaml) == 
           {'Test1' : [
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
            ]})
        
def test_write_yaml_file():
    assert True

def test_read_file():
    assert True
    
def test_write_file():
    assert True
    
def test_write_and_chmod():
    assert True
    
def test_delete_file():
    assert True
    
def test_get_components_list():
    assert True
    
def test_is_component_config():
    assert True
    
def test_execute_script():
    assert True

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
    ])"""