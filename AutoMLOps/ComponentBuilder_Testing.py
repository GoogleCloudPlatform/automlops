from . import ComponentBuilder

def test_formalize():
    assert True
    
def test_create_task():
    assert True
    
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
    assert True