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

"""Creates generic component, pipeline, and services objects."""

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# pylint: disable=line-too-long
# pylint: disable=broad-exception-caught

import ast
import inspect
from typing import Callable, List, Optional, TypeVar, Union

import docstring_parser

from google_cloud_automlops.utils.utils import (
    get_defaults,
    get_function_source_definition,
)
from google_cloud_automlops.utils.constants import (
    BASE_DIR,
    DEFAULT_PIPELINE_NAME,
)
from google_cloud_automlops.utils.enums import Parameter

T = TypeVar('T')


class BaseComponent():
    """The Component object represents a component defined by the user.
    """
    def __init__(self,
                 func: Optional[Callable] = None,
                 packages_to_install: Optional[List[str]] = None):
        """Initiates a generic Component object created out of a function holding
        all necessary code.

        Args:
            func (Optional[Callable]): The python function to create a component from. The function
                should have type annotations for all its arguments, indicating how it is intended to
                be used (e.g. as an input/output Artifact object, a plain parameter, or a path to a
                file). Defaults to None.
            packages_to_install (Optional[List[str]]): A list of optional packages to install before
                executing func. These will always be installed at component runtime. Defaults to None.

        Raises:
            ValueError: The parameter `func` is not an existing function.
        """

        # Confirm the input is an existing function
        if not inspect.isfunction(func):
            raise ValueError(f'{func} must be of type function.')

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

        # Instantiate attributes to be set during build
        self.defaults = None

    def build(self):
        """Instantiates an abstract built method to create and write task files. Also reads in
        defaults file to save default arguments to attributes.

        Raises:
            NotImplementedError: The subclass has not defined the `build` method.
        """
        self.defaults = get_defaults()

    def _get_function_return_types(self) -> list:
        """Returns a formatted list of function return types.

        Returns:
            list: return value list with types converted to kubeflow spec.

        Raises:
            Exception: If return type is provided and not a NamedTuple.
        """
        # Extract return type annotation of function
        annotation = inspect.signature(self.func).return_annotation

        # Ensures return type is not optional
        if self.maybe_strip_optional_from_annotation(annotation) is not annotation:
            raise TypeError('Return type cannot be Optional.')

        # No annotations provided, return none
        # pylint: disable=protected-access
        if annotation == inspect._empty:
            return None

        # Checks if the function's return type annotation is a valid NamedTuple
        if not (hasattr(annotation,'__annotations__') and isinstance(annotation.__annotations__, dict)):
            raise TypeError(f'''Return type hint for function "{self.name}" must be a NamedTuple.''')

        # Creates a parameter object for each parameter returned by component
        outputs: List[Parameter] = []
        for name, type_ in annotation.__annotations__.items():
            p = Parameter(
                name=name,
                type=type_,
                description=None
            )
            outputs.append(p)
        return outputs

    def _get_function_parameters(self) -> list:
        """Returns a formatted list of parameters.

        Returns:
            list: Params list with types converted to kubeflow spec.

        Raises:
            Exception: Parameter type hints are not provided.
        """
        # Extract function parameter names and their descriptions from the function's docstring
        signature = inspect.signature(self.func)
        parameters = list(signature.parameters.values())
        parsed_docstring = docstring_parser.parse(inspect.getdoc(self.func))
        doc_dict = {p.arg_name: p.description for p in parsed_docstring.params}

        # Extract parameter metadata
        parameter_holder: List[Parameter] = []
        for param in parameters:
            p = Parameter(
                name=param.name,
                type=self.maybe_strip_optional_from_annotation(
                param.annotation),
                description=doc_dict.get(param.name)
            )
            parameter_holder.append(p)
            # pylint: disable=protected-access
            if p.type == inspect._empty:
                raise TypeError(
                    f'''Missing type hint for parameter "{p.name}". '''
                    f'''Please specify the type for this parameter.''')
        return parameter_holder

    def maybe_strip_optional_from_annotation(self, annotation: T) -> T:
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


class BasePipeline():
    """The Pipeline object represents a component defined by the user.
    """

    def __init__(self,
                 func: Optional[Callable] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 comps_dict: dict = None):
        """Initiates a pipeline object created out of a function holding
        all necessary code.

        Args:
            func (Optional[Callable]): The python function to create a pipeline from. The function
                should have type annotations for all its arguments, indicating how it is intended to
                be used (e.g. as an input/output Artifact object, a plain parameter, or a path to a
                file). Defaults to None.
            name (Optional[str]): The name of the pipeline. Defaults to None.
            description (Optional[str]): Short description of what the pipeline does. Defaults to None.
            comps_list (dict): Dictionary of potential components for pipeline to utilize imported
                as the global held in AutoMLOps.py. Defaults to None.
        """
        # Instantiate and set key pipeline attributes
        self.func = func
        self.func_name = func.__name__
        self.name = DEFAULT_PIPELINE_NAME if not name else name
        self.description = description
        self.src_code = get_function_source_definition(self.func)
        self.comps = self.get_pipeline_components(func, comps_dict)

        # Instantiate attributes to be set at build process
        self.defaults = None
        self.custom_training_job_specs = None
        self.pipeline_params = None

    def build(self,
              pipeline_params: dict,
              custom_training_job_specs: Optional[List] = None):
        """Instantiates an abstract built method to create and write pipeline files. Also reads in
        defaults file to save default arguments to attributes.

        Files created must include:
            1. README.md
            2. Dockerfile
            3. Requirements.txt

        Args:
            custom_training_job_specs (dict): Specifies the specs to run the training job with.
            pipeline_params (Optional[List]): Dictionary containing runtime pipeline parameters.
                Defaults to None.

        Raises:
            NotImplementedError: The subclass has not defined the `build` method.
        """
        # Save parameters as attributes
        self.custom_training_job_specs = custom_training_job_specs
        self.pipeline_params = pipeline_params

        # Extract additional attributes from defaults file
        self.defaults = get_defaults()

    def get_pipeline_components(self,
                                pipeline_func: Callable,
                                comps_dict: dict) -> list:
        """Returns a list of components used within a given pipeline.

        Args:
            pipeline_func (Callable): Pipeline function.
            comps_dict (dict): List of potential components to use within pipeline.

        Returns:
            List: Components from comps_dict used within the pipeline_func.
        """
        # Retrieves pipeline source code and parses it into an Abstract Syntax Tree (AST)
        code = inspect.getsource(pipeline_func)
        ast_tree = ast.parse(code)

        #  Iterates through AST, finds function calls to components that are in comps_dict
        comps_list = []
        for node in ast.walk(ast_tree):
            try:
                if isinstance(node, ast.Call) and node.func.id in comps_dict.keys():
                    comps_list.append(comps_dict[node.func.id])
            except Exception:
                pass
        return comps_list


class BaseFuturePipeline():
    """Placeholder for future pipeline object that will be created out of a list of components.
    """
    def __init__(self, comps: list) -> None:
        self.comps = comps
        self.names = [comp.name for comp in self.comps]


class BaseServices():
    """The Services object will contain code within the services/ dir.
    """

    def __init__(self) -> None:
        """Instantiates a generic Services object.
        """
        self.defaults = None

        # Set directory for files to be written to
        self.submission_service_base_dir = BASE_DIR + 'services/submission_service'

    def build(self):
        """Constructs and writes files related to submission services and model monitoring. 
        
            Files created under AutoMLOps/:
                services/
                    submission_service/
                        Dockerfile
                        main.py
                        requirements.txt
                model_monitoring/ (if requested)
                    monitor.py
                    requirements.txt
        """
        # Extract additional attributes from defaults file
        self.defaults = get_defaults()

        # Set directory for files to be written to
        self.submission_service_base_dir = BASE_DIR + 'services/submission_service'

        # Build services files
        self._build_submission_services()

        # Setup model monitoring
        if self.defaults.gcp.setup_model_monitoring:
            self._build_monitoring()

    def _build_monitoring(self):
        """Abstract method to create the model monitoring files.

        Raises:
            NotImplementedError: The subclass has not defined the `_build_monitoring` method.
        """
        raise NotImplementedError('Subclass needs to define this')

    def _build_submission_services(self):
        """Abstract method to create the Dockerfile, requirements.txt, and main.py files of the
            services/submission_service directory.

        Raises:
            NotImplementedError: The subclass has not defined the `_build_submission_services` method.
        """
        raise NotImplementedError('Subclass needs to define this.')
