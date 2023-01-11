from setuptools import setup

setup(
    name='AutoMLOps',
    version='1.0.0',    
    description='AutoMLOps is a tool that generates a production-style \
        MLOps pipeline from Jupyter Notebooks.',
    url='https://source.cloud.google.com/sandbox-srastatter/1-ClickMLOps',
    author='Sean Rastatter',
    author_email='srastatter@google.com',
    license='Apache-2.0',
    packages=['AutoMLOps'],
    install_requires=['autoflake==2.0.0',
                      'docopt==0.6.2',
                      'ipython==7.34.0',
                      'pipreqs==0.4.11',
                      'pyflakes==3.0.1',
                      'PyYAML==5.4.1',
                      'yarg==0.1.9'],
    classifiers=[
        'Development Status :: Draft',
        'Intended Audience :: data science practitioners',
        'License :: OSI Approved :: Apache-2.0',  
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',])