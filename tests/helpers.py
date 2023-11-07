import subprocess
import re

def assert_repository_exists(repository_name):
    """
    Helper function to assert that a specified repository exists.

    Args:
        repository_name: The name of the repository to check.

    Raises:
        AssertionError: If the repository doesn't exist.
    """
    output = subprocess.run([f"gcloud source repos list --filter={repository_name}"], shell=True, capture_output=True, text=True).stdout
    pattern = r"\b" + re.escape(repository_name) + r"\b"
    match = re.search(pattern, output)

    # Access the matched string using group()
    matched_repository_name = match.group() if match else None
    assert matched_repository_name == repository_name, f"Repository '{repository_name}' doesn't exist."