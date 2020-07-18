from setuptools import setup

setup(
    name='atpparser',
    url='https://github.com/jladan/package_demo',
    author='Nathan Esau',
    author_email='nathanesau1@gmail.com',
    packages=['atpparser'],
    install_requires=['bs4'],
    version='0.1',
    license='MIT',
    description='Package which scraper information from atptour website',
    long_description=open('README.txt').read(),
)