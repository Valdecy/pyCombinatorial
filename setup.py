from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

setup(
    name='pyCombinatorial',
    version='1.7.9',
    license='GNU',
    author='Valdecy Pereira',
    author_email='valdecy.pereira@gmail.com',
    url='https://github.com/Valdecy/pyCombinatorial',
    packages=find_packages(),
    install_requires=[
        'networkx',
        'numpy',
        'plotly',
		'scipy'
    ],
    description='A library to solve TSP (Travelling Salesman Problem) using Exact Algorithms, Heuristics and Metaheuristics',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
