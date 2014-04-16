# coding=utf8

from setuptools import setup, find_packages

setup(
    name='fuzzy-fabric',
    version='0.6',

    author='Dmitry Voronin',
    author_email='dimka665@gmail.com',

    url='https://github.com/dimka665/fuzzy-fabric',
    description='Fuzzy Functions For Fabric',

    packages=find_packages(),
    install_requires=[
        'Fabric',
        'virtualenv',
        'virtualenvwrapper',
    ],

    license='MIT License',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='fuzzy functions for fabric',
)
