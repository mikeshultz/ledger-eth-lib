import sys
import shutil
import ledgereth
from os import path
from setuptools import Command, setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call, CalledProcessError

pwd = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(pwd, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def requirements_to_list(filename):
    return [dep for dep in open(path.join(pwd, filename)).read().split('\n') if (
        dep and not dep.startswith('#')
    )]


setup(
    name='ledgereth',
    version=ledgereth.__version__,
    description='Library to interface with ledger-app-eth on Ledger hardware wallets',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mikeshultz/ledger-eth-lib',
    author=ledgereth.__author__,
    author_email=ledgereth.__email__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='solidity ethereum development',
    packages=find_packages(exclude=['docs', 'tests', 'scripts', 'build']),
    install_requires=requirements_to_list('requirements.txt'),
    extras_require={
        'dev': requirements_to_list('requirements.dev.txt'),
    },
    package_data={
        '': [
            'README.md',
            'LICENSE',
        ],
    }
)
