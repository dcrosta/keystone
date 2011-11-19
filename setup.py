from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
    name='Keystone',
    description='A very simple, yet flexible, dynamic website framework',
    version='0.1',
    author='Dan Crosta',
    author_email='dcrosta@late.am',
    license='BSD',
    url='https://github.com/dcrosta/keystone',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
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
