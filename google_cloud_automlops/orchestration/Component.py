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

"""Creates a generic component object."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long

from abc import ABC, abstractmethod
import docstring_parser
import inspect
from typing import Callable, List, Optional, TypeVar, Union

from google_cloud_automlops.utils.constants import GENERATED_DEFAULTS_FILE
from google_cloud_automlops.utils.utils import (
    get_function_source_definition,
    read_yaml_file
)

T = TypeVar('T')


class Component(ABC):
    """The Component object represents a component defined by the user.

    Args:
        ABC: Abstract class
    """

    def __init__(self,
                 func: Optional[Callable] = None,
                 packages_to_install: Optional[List[str]] = None):
        """Initiates a generic Component object created out of a function holding
        all necessary code.

        Args:
            func: The python function to create a component from. The function
                should have type annotations for all its arguments, indicating how
                it is intended to be used (e.g. as an input/output Artifact object,
                a plain parameter, or a path to a file).
            packages_to_install: A list of optional packages to install before
                executing func. These will always be installed at component runtime.

        Raises:
            ValueError: Confirms that the input is an existing function.
        """

        # Confirm the input is an existing function
        if not inspect.isfunction(func):
            raise ValueError(f"{func} must be of type function.")

        # Set simple attributes of the component function
        self.func = func
        self.name = func.__name__
        self.packages_to_install = [] if not packages_to_install else packages_to_install

        # Parse the docstring for description 
        self.parsed_docstring = docstring_parser.parse(inspect.getdoc(func))
        self.description = self.parsed_docstring.short_description

        # Process and extract details from passed function
        self.parameters = self._get_function_parameters()
        self.return_types = self._get_function_return_types()
        self.src_code = get_function_source_definition(self.func)

    @abstractmethod
    def build(self):
        """Instantiates an abstract built method to create and write task files. Also
        reads in defaults file to save default arguments to attributes.
        """
        defaults = read_yaml_file(GENERATED_DEFAULTS_FILE)
        self.artifact_repo_location = defaults['gcp']['artifact_repo_location']
        self.artifact_repo_name = defaults['gcp']['artifact_repo_name']
        self.project_id = defaults['gcp']['project_id']
        self.naming_prefix = defaults['gcp']['naming_prefix']

    def _get_function_return_types(self) -> list:
        """Returns a formatted list of function return types.

        Returns:
            list: return value list with types converted to kubeflow spec.
        Raises:
            Exception: If return type is provided and not a NamedTuple.
        """
        # TODO: COMMENT
        annotation = inspect.signature(self.func).return_annotation
        if maybe_strip_optional_from_annotation(annotation) is not annotation:
            raise TypeError('Return type cannot be Optional.')

        # No annotations provided
        # pylint: disable=protected-access
        if annotation == inspect._empty:
            return None

        if not (hasattr(annotation,'__annotations__') and isinstance(annotation.__annotations__, dict)):
            raise TypeError(f'''Return type hint for function "{self.name}" must be a NamedTuple.''')

        # TODO: COMMENT
        outputs = []
        for name, type_ in annotation.__annotations__.items():
            metadata = {}
            metadata['name'] = name
            metadata['type'] = type_
            metadata['description'] = None
            outputs.append(metadata)
        return outputs

    def _get_function_parameters(self) -> list:
        """Returns a formatted list of parameters.

        Returns:
            list: Params list with types converted to kubeflow spec.
        Raises:
            Exception: If parameter type hints are not provided.
        """
        #TODO: COMMENT?
        signature = inspect.signature(self.func)
        parameters = list(signature.parameters.values())
        parsed_docstring = docstring_parser.parse(inspect.getdoc(self.func))
        doc_dict = {p.arg_name: p.description for p in parsed_docstring.params}

        # Extract parameter metadata
        parameter_holder = []
        for param in parameters:
            metadata = {}
            metadata['name'] = param.name
            metadata['description'] = doc_dict.get(param.name)
            metadata['type'] = maybe_strip_optional_from_annotation(
                param.annotation)
            parameter_holder.append(metadata)
            # pylint: disable=protected-access
            if metadata['type'] == inspect._empty:
                raise TypeError(
                    f'''Missing type hint for parameter "{metadata['name']}". '''
                    f'''Please specify the type for this parameter.''')
        return parameter_holder

def maybe_strip_optional_from_annotation(annotation: T) -> T:
    """Strips 'Optional' from 'Optional[<type>]' if applicable.
    For example::
        Optional[str] -> str
        str -> str
        List[int] -> List[int]
    Args:
        annotation: The original type annotation which may or may not has `Optional`.
    Returns:
        The type inside Optional[] if Optional exists, otherwise the original type.
    """
    if getattr(annotation, '__origin__', None) is Union and annotation.__args__[1] is type(None):
        return annotation.__args__[0]
    else:
        return annotation
