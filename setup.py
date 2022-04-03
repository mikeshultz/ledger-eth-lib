from importlib.machinery import SourceFileLoader
from pathlib import Path
from subprocess import check_call

from setuptools import find_packages, setup
from setuptools.command.develop import develop

pwd = Path(__file__).parent

# Get the long description from the README file
with pwd.joinpath("README.md").open(encoding="utf-8") as f:
    long_description = f.read()


def requirements_to_list(filename):
    return [
        dep
        for dep in pwd.joinpath(filename).open(encoding="utf-8").read().split("\n")
        if (dep and not dep.startswith("#"))
    ]


class LintCommand(develop):
    """Run linting"""

    def run(self):
        try:
            check_call("black .".split())
            check_call("isort --profile black .".split())
            check_call("autoflake -ir .".split())
        except CalledProcessError as err:
            if "non-zero" in str(err):
                print("linting failed with warnings", file=sys.stderr)
                sys.exit(1)


# Allows us to import the file without executing imports in module __init__
meta = SourceFileLoader("meta", str(pwd.joinpath("ledgereth/_meta.py"))).load_module()

setup(
    name="ledgereth",
    version=meta.version,
    description="Library to interface with ledger-app-eth on Ledger hardware wallets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mikeshultz/ledger-eth-lib",
    author=meta.author,
    author_email=meta.email,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="solidity ethereum development",
    packages=find_packages(exclude=["docs", "tests", "scripts", "build"]),
    install_requires=requirements_to_list("requirements.txt"),
    extras_require={
        "dev": requirements_to_list("requirements.dev.txt"),
        "docs": requirements_to_list("requirements.docs.txt"),
    },
    package_data={
        "": [
            "README.md",
            "LICENSE",
        ],
    },
    cmdclass={
        "lint": LintCommand,
    },
)
