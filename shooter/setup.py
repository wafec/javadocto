from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='Shooter',
    version='0.9dev',
    packages=['shooter'],
    licence='BSD',
    long_description=read('README.txt'),
    install_requires = [
        'pyyaml',
        'munch'
    ],
    python_requires='>=3.7'
)