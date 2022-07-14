from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

setup(
    name='pyCombinatorial',
    version='1.1.2',
    license='GNU',
    author='Valdecy Pereira',
    author_email='valdecy.pereira@gmail.com',
    url='https://github.com/Valdecy/pyCombinatorial',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'plotly'
    ],
    description='A Metaheuristics Library for TSP problems',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
