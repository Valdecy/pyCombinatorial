from pathlib import Path
from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text(encoding='utf-8')

setup(
    name='pycombinatorial',
    version='2.2.5',
    license='GNU',
    author='Valdecy Pereira',
    author_email='valdecy.pereira@gmail.com',
    url='https://github.com/Valdecy/pyCombinatorial',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pyCombinatorial.web': [
            'README.md',
            'index.html',
            'css/*.css',
            'js/*.js',
            'js/core/*.js',
            'js/algorithms/*.js',
        ]
    },
    install_requires=[
        'folium',
        'networkx',
        'numpy',
        'plotly',
        'scipy',
    ],
    entry_points={
        'console_scripts': [
            'pycombinatorial-web=pyCombinatorial.web:launch_web',
        ]
    },
    description='A library to solve TSP (Travelling Salesman Problem) using Exact Algorithms, Heuristics, Metaheuristics and Reinforcement Learning',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
