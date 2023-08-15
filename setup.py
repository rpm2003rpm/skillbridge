
from setuptools import setup, find_packages

setup(
    name='skillbridge',
    version='1.1',
    packages=find_packages(),
    install_requires=[
        #'functools',
        'pytest',
        'regex',
        'selection',
        'sockets',
        'dataclasses',
        #'jsonlib',
        'typing'
    ]
)


