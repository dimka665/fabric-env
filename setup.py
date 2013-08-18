from setuptools import setup
import os

name = 'fabric-env'
package = 'fabric_env'
version = '0.5.4'

url = 'https://github.com/dimka665/fabric_env'
author = 'Dmitry Voronin'
author_email = 'dimka665@gmail.com'
license_ = 'BSD'

description = 'Accessory classes and functions for Fabric'
long_description = open('README.rst').read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


setup(
    name=name,
    version=version,
    url=url,
    license=license_,
    description=description,
    long_description=long_description,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data=get_package_data(package),
)


