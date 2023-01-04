"""
AutoMLOps

AutoMLOps is a tool that generates a production-style MLOps pipeline 
from Jupyter Notebooks. The tool currently operates as a local package 
import, with the end goal of becoming a Jupyter plugin to Vertex 
Workbench managed notebooks. The tool will generate yaml-component 
definitions, complete with Dockerfiles and requirements.txts for all 
Kubeflow components defined in a notebook. It will also generate a 
series of directories to support the creation of Vertex Pipelines.
"""

__version__ = "1.0.0"
__author__ = 'Sean Rastatter'
__credits__ = 'Google'