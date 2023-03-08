from . import ComponentBuilder

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
                        'image': 'docker_container',
                        'command': 'my_command'
                    }
            }
    }
)

def test_formalize():
    assert True
    
def test_create_task(tmpdir):
    
    actual = ComponentBuilder.create_task(component_spec=COMPONENT_DICT,
                                          task_filepath=tmpdir,
                                          use_kfp_spec=False)
    
    assert actual
    
def test_create_component():
    assert True
    
def test_create_component_scaffold():
    assert True
    
def test_get_func_definition(): 
    
    expected = (
        f'\n'
        f'def myFunc(\n'
        f'''    my_str_param: str,\n'''
        f'''    my_int_param: int,\n'''
        f'):\n'
        f'    """This is a test function\n'
        f'\n'
        f'    Args:\n'
        f'''        my_str_param: Test string parameter.,\n'''
        f'''        my_int_param: Test int parameter.,\n'''
        f'    """'
    )
    
    actual = ComponentBuilder.get_func_definition(
        name = 'myFunc',
        params = [
            {
                'name': 'my_str_param',
                'type': str,
                'description': 'Test string parameter.'
            },
            {
                'name': 'my_int_param',
                'type': int,
                'description': 'Test int parameter.'
            }
            ],
        description = 'This is a test function'
    )
    
    # Do we need to test for if there is no description if ideally that's not happening at this point?
    
    assert expected == actual
    
    
def test_filter_and_indent_cell():
    
    code_cell = (
        'AutoMLOps.makeComponent('
        '   def my_func():'
        '       #test'
    )
    
    for line in code_cell.splitlines():
        print(line)
    
    assert code_cell == True
    
