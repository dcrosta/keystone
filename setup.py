from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
    name='keystone',
    install_requires=[
        'werkzeug',
        'jinja2',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'keystone = keystone.main:serve',
        ],
    }
)
