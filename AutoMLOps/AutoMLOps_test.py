from . import AutoMLOps

##################################################################################################################################
# AutoMLOps Testing
##################################################################################################################################

###############
# Generate
###############

# Given project_id = "my-proj", bucket = my-proj-bucket

# Given gs_bucket_name = "my-bucket", bucket = "my-bucket"

# Given project_id "my-proj", pipeline runner sa = "vertex-pipelines@my-proj.iam.gserviceaccount.com"

# Given pipeline runna sa = "my-runner@my-proj.iam.gserviceaccount.com", pipeline runner = same

# Confirm directories were created as expected, no more no less

# Confirm config file was created, some tests of input vs output

# Confirm scripts were created, tests of input vs output

# Confirm cloudbuild config was created, some tests of input vs output

# Confirm pipeline was copied, that the two are equal

def test_go():
    assert True
    
def test_generate():
    assert True

def test_run():
    assert True
    
def test_resources_generation_manifest():
    assert True
    
def test_copy_pipeline():
    assert True
    
def test_push_to_csr():
    assert True

def test_create_default_config():
    assert True
    
def test_create_scripts():
    assert True
     
def test_create_resources_scripts():
    assert True
    
def test_create_cloudbuild_config():
    assert True
    
def test_autoflake_srcfiles():
    assert True
    
def test_create_requirements():
    assert True
    
def test_create_dockerfile():
    assert True
    
def test_makeComponent():
    assert True

def test_makePipeline():
    assert True


