from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="OpenHurricane",
    version='0.9dev',
    packages=['openhurricane', 'tests'],
    licence='BSD',
    long_description=read('README.txt'),
    install_requires=read('requirements.txt').split('\n'),
    python_requires='>=3.7'
)