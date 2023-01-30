import pytest, pathlib, os
from . import BuilderUtils

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
    assert True
    
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
        
    # Add test for an error reading a yaml file
            
def test_write_yaml_file():
    # Can we write a yaml file and then read it back in to confirm it matches expected?
    # I.e. can we assume that tests that were run earlier in the file are correct and use them?
    assert True

def test_read_file():
    assert True
    
def test_write_file():
    # What modes should be tested
    assert True
    
def test_write_and_chmod():
    assert True
    
def test_delete_file(tmpdir):
    
    f = open(f"{tmpdir}/myfile.txt", "x")
    
    BuilderUtils.delete_file(f"{tmpdir}/myfile.txt")
    
    assert not os.path.exists(f"{tmpdir}/myfile.txt")
    
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
    ])